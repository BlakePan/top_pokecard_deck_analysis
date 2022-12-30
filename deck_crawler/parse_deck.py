import concurrent.futures
import copy
import logging
import os
import re
import threading
import time
import unicodedata
from typing import Any, Dict, List, Tuple, Union

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from .deck_category_helper import find_categories

# Set up logging to a file
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=f"logs/{os.path.basename(__file__)}.log",
    filemode="w",
)
logger = logging.getLogger(__name__)


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--start-maximized")

# https://blog.csdn.net/sxf1061700625/article/details/124263680
# disable images
chrome_options.add_argument("blink-settings=imagesEnabled=false")
chrome_options.add_argument("--disable-images")
# disable javascripts
chrome_options.add_argument("--disable-javascript")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-java")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--disable-blink-features")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--incognito")


def full2half(c: str) -> str:
    """Converts a full-width character to a half-width character.

    Args:
        c (str): The full-width character to be converted.

    Returns:
        str: The half-width equivalent of the input character.
    """
    return unicodedata.normalize("NFKC", c)


def wait_loading_circle(driver, timeout: int = 20):
    """Waits for an element with the class `sk-circle-container`
    (a loading circle) to become invisible on the page.

    Args:
        driver (WebDriver): A Selenium web driver instance.
        timeout (int, optional): The maximum time to wait for the element
        to become invisible. Defaults to 20.

    Raises:
        TimeoutError: If the element does not become invisible
        within the specified timeout.
    """
    WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//div[@class='sk-circle-container']")
        )
    )


def extract_card(cards: List[str]) -> Dict[str, int]:
    """Extracts information about cards from a list of strings
    and returns the information as a dictionary.

    Args:
        cards (List[str]): A list of strings containing card information.

    Returns:
        Dict[str, int]: A dictionary with keys representing card names
        and values representing card counts.
    """
    extracted_card_info = {}

    for card_string in cards[1:]:
        card_string = card_string.split(" ")
        character_index = -1
        for character in ["（", "("]:
            if character in card_string[0]:
                character_index = card_string[0].find(character)

        # if there is a left parenthesis in the card name,
        # then the card name will be modified for removing chars
        # including and after the left parenthesis
        # otherwise, just keep the same card name
        card_string[0] = (
            card_string[0][:character_index]
            if character_index != -1
            else card_string[0]
        )
        extracted_card_info[card_string[0]] = int(card_string[-1][:-1])

    return extracted_card_info


def reassign_category(decks: dict) -> dict:
    """Reassigns a category to each deck in a dictionary of decks.

    The category for each deck is determined by calling the
    find_categories function with the "pokemons", "tools", and "energies"
    fields of the deck.

    Args:
        decks (dict): A dictionary of decks, with the keys as
        categories and the values as lists of decks.

    Returns:
        dict: A dictionary of decks, with the keys as
        categories and the values as lists of decks.
    """
    new_decks = {}

    for category in decks.keys():
        for deck in decks[category]:
            assigned_categories = find_categories(
                deck["pokemons"], deck["tools"], deck["energies"]
            )

            for assigned_category in assigned_categories:
                if assigned_category not in new_decks:
                    new_decks[assigned_category] = []

                new_decks[assigned_category].append(deck)

    return new_decks


def parse_deck(deck_code: str = None, deck_link: str = None) -> Tuple:
    """Parses a deck and returns the card information
    as a tuple of dictionaries.

    Args:
        deck_code (str, optional): The code of the deck to parse.
        deck_link (str, optional): The URL of the deck to parse.

    Returns:
        Tuple[Dict[str, int], ...]:
            A tuple of dictionaries with keys representing card names and
            values representing card counts.
            The dictionaries represent the Pokemon cards, tool cards,
            supporter cards, stadium cards, and energy cards, respectively.
    """
    # Return early if neither a deck code nor a deck link is provided
    if not deck_code and not deck_link:
        return

    # Initialize dictionaries to store the card information
    pokemon_dict = {}  # {card_name: no.cards}
    tool_dict = {}
    supporter_dict = {}
    stadium_dict = {}
    energy_dict = {}

    # Use the deck link if provided,
    # otherwise generate the URL using the deck code
    url = (
        deck_link
        if deck_link
        else f"https://www.pokemon-card.com/deck/confirm.html/deckID/{deck_code}/"
    )

    with webdriver.Chrome(options=chrome_options) as driver:
        # Initialize the web driver
        driver.implicitly_wait(2)  # seconds

        try:
            # Navigate to the deck page and click the "list view" button
            driver.get(url)
            driver.find_element(By.ID, "deckView01").click()  # Click リスト表示
            # Find the element containing the card information
            elems = driver.find_element(By.ID, "cardListView").find_elements(
                By.CLASS_NAME, "Grid_item"
            )

            for e in elems:
                if "ポケモン (" in e.text:
                    """
                    example:

                    ポケモン (11)
                    ジュラルドンVMAX
                    S8b
                    253/184
                    3枚
                    """
                    cards = e.text.split("\n")
                    for i in range(1, len(cards), 4):
                        card_name = cards[i]
                        card_code = cards[i + 1] + "/" + cards[i + 2]
                        # workaround for repeated name, TODO: add card code column
                        if card_name == "カイオーガ" and card_code == "S4a/036/190":
                            card_name = "AR カイオーガ"

                        card_numbers = int(cards[i + 3][:-1])
                        pokemon_dict[card_name] = card_numbers
                else:
                    """
                    example:

                    グッズ (19)
                    クイックボール 3枚
                    """
                    cards = e.text.split("\n")
                    res = extract_card(cards)
                    if "グッズ (" in e.text:
                        tool_dict = res
                    elif "サポート (" in e.text:
                        supporter_dict = res
                    elif "スタジアム (" in e.text:
                        stadium_dict = res
                    elif "エネルギー (" in e.text:
                        energy_dict = res
        except Exception as e:
            logger.info(f"An error occurred while parsing the deck: {e}")
            logger.debug(e)
            return None

    return pokemon_dict, tool_dict, supporter_dict, stadium_dict, energy_dict


def crawl_deck_pages(
    deck_metas: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Crawl the pages of the given deck metadata in parallel using threads.

    Parameters:
    - deck_metas (List[Dict[str, Any]]):
    a list of dictionaries containing metadata for each deck,
    including the url, deck code, rank, number of people, and date

    Returns:
    - Dict[str, List[Dict[str, Any]]]:
    a dictionary of lists of dictionaries containing
    the parsed information for each deck, grouped by category
    """

    # Create the shared dictionary
    results = {}
    lock = threading.Lock()

    # Initialize an empty list to hold the results
    temp_results = []

    def crawl_deck_page(deck_meta):
        url = deck_meta["url"]
        deck_code = deck_meta["deck_code"]
        rank = deck_meta["rank"]
        num_players = deck_meta["num_players"]
        date = deck_meta["date"]

        t1 = time.time()
        ret = parse_deck(deck_link=url)
        t2 = time.time()
        logger.debug(f"parse_deck Time diff: {t2-t1}")

        if ret is not None:
            pokemon_dict, tool_dict, supporter_dict, stadium_dict, energy_dict = ret
        else:
            logger.info(f"parse_deck Fail, {url}")
            return

        temp_results.append(
            {
                "deck_link": url,
                "deck_code": deck_code,
                "pokemons": pokemon_dict,
                "tools": tool_dict,
                "supporters": supporter_dict,
                "stadiums": stadium_dict,
                "energies": energy_dict,
                "rank": rank,
                "num_players": num_players,
                "date": date,
            }
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Create a task for each deck
        threads = []
        for deck_meta in deck_metas:
            task = executor.submit(crawl_deck_page, deck_meta)
            threads.append(task)

        # Wait for all tasks to complete
        concurrent.futures.wait(threads)

    # Update the results dictionary with the entire temp_results list
    with lock:
        for result in temp_results:
            categories = find_categories(
                result["pokemons"], result["tools"], result["energies"]
            )
            for category in categories:
                if category not in results:
                    results[category] = []
                results[category].append(result)

    return results


def parse_deck_meta(deck_elem: WebElement, skip_codes: List[str]) -> Dict[str, Any]:
    """Parses metadata for a deck from a WebElement
    representing a deck in a deck list table.

    Parameters:
    deck_elem (WebElement): WebElement representing
    a deck in a deck list table.

    skip_codes (List[str]): List of deck codes to skip.

    Returns:
    Dict[str, Any]: Dictionary containing metadata for the deck.
    """

    # Extract the URL for the deck element
    url = (
        deck_elem.find_element(By.CLASS_NAME, "deck")
        .find_element(By.TAG_NAME, "a")
        .get_property("href")
    )

    # Extract the deck code from the URL
    deck_code = url.split("/")[-1]
    if deck_code in skip_codes:
        return None

    # Extract the rank of the deck element
    tag = deck_elem.find_element(By.TAG_NAME, "td")
    rank = int(tag.get_attribute("class").split("-")[-1])

    return {
        "url": url,
        "deck_code": deck_code,
        "rank": rank,
    }


def parse_event_to_deck(
    event_link: str,
    num_players: int,
    decks: Dict,
    skip_codes: List[str],
    num_pages: int = 1,
) -> None:
    """
    Parse a given event page and collect metadata of available decks.

    Parameters:
    - event_link (str): the link of the event page
    - num_players (int): the number of players who participated in the event
    - decks (Dict): the dictionary to store the collected metadata
    - skip_codes (List[str]): the list of deck codes to skip
    - num_pages (int): the number of pages to parse (default: 1).
    If num_pages < 0, parse all pages.
    If num_pages = 0, no parsing.
    If num_pages = 1, parse pages for top-8.
    If num_pages = 2, parse pages for top-16.
    And so on.

    Returns:
    None
    """

    with webdriver.Chrome(options=chrome_options) as driver:
        # Initialize the web driver
        driver.implicitly_wait(2)  # seconds

        # Navigate to the event page
        driver.get(event_link)
        date_str = driver.find_element(By.CLASS_NAME, "date-day").text

        t1 = time.time()
        deck_metas = []
        while num_pages:
            # Collect metadata of available decks
            deck_elems = driver.find_elements(By.CLASS_NAME, "c-rankTable-row")
            for deck_idx, deck_elem in enumerate(deck_elems):
                try:
                    deck_meta = parse_deck_meta(deck_elem, skip_codes)
                    if deck_meta is None:
                        raise Exception(
                            "This deck is parsed before,"
                            "or there is an error while parsing deck meta "
                        )
                    deck_meta["num_players"] = num_players
                    deck_meta["date"] = date_str

                    deck_metas.append(deck_meta)
                except Exception as e:
                    logger.debug(e)
                    logger.debug(event_link)
                    logger.debug(f"skip deck no. {deck_idx}")

            # nevigate to the next page
            try:
                num_pages -= 1
                if num_pages:
                    driver.find_element(By.CLASS_NAME, "btn.next").click()
                    wait_loading_circle(driver)
            except Exception as e:
                if isinstance(e, TimeoutError):
                    logger.info("Wait for loading circle Timeout")
                elif isinstance(e, NoSuchElementException):
                    if num_pages:
                        logger.info("Next deck page not found")
                    else:
                        logger.info("There is no next deck page")
                logger.debug(e)
                logger.debug(event_link)
                break
        t2 = time.time()
        logger.debug(f"Page Time diff part1: {t2-t1}")

        # wait for results
        logger.debug(deck_metas)
        t1 = time.time()
        results = crawl_deck_pages(deck_metas)
        t2 = time.time()
        logger.debug(f"Page Time diff part2: {t2-t1}")

        # update crawl results to decks
        for category in results:
            if category not in decks:
                decks[category] = []
            decks[category] += results[category]


def get_event_meta(event_element: WebElement) -> Dict[str, Union[int, str]]:
    """Extract metadata for an event from the given event element.

    Parameters:
        event_element (WebElement):
        The WebElement representing an event on a webpage.

    Returns:
        Dict[str, Union[int, str]]:
        A dictionary containing the metadata for the event.
        The keys of the dictionary are 'num_players' and 'event_link',
        and the values are the corresponding integer value for
        the number of players and the string value for the event link.
    """

    num_players_str = event_element.find_element(By.CLASS_NAME, "capacity").text
    num_players = re.findall(r"\d+", num_players_str)
    num_players = (
        int(num_players[0])
        if isinstance(num_players, List) and len(num_players) == 1
        else -1
    )

    event_link = event_element.get_attribute("href")

    return {
        "num_players": num_players,
        "event_link": event_link,
    }


def parse_events_from_official(
    decks: Dict,
    skip_codes: List[int] = None,
    result_page_limit: int = 10,
    event_page_limit: int = 100,
    deck_page_limit: int = 1,
) -> None:
    """Parses CL event links and metadata from the official website.

    Args:
        decks (Dict): A dictionary to store the parsed CL event data.

        skip_codes (List[int], optional):
        A list of deck codes to skip. Defaults to None.

        result_page_limit (int, optional):
        The maximum number of result pages to parse. Defaults to 10.

        event_page_limit (int, optional):
        The maximum number of event pages to parse. Defaults to 100.

        deck_page_limit (int, optional):
        The maximum number of deck pages to parse for each event.
        If num_pages < 0, parse all pages.
        If num_pages = 0, no parsing.
        If num_pages = 1, parse pages for top-8.
        If num_pages = 2, parse pages for top-16.
        And so on.
    """
    skip_codes = [] if skip_codes is None else skip_codes

    # parse CL event links from official website
    url = "https://players.pokemon-card.com/event/result/list"
    with webdriver.Chrome(options=chrome_options) as driver:
        try:
            # Initialize the web driver
            driver.implicitly_wait(2)  # seconds
            # Navigate to the result page
            driver.get(url)
        except Exception as e:
            if isinstance(e, WebDriverException):
                logger.info("WebDriverException when parsing result link")
            else:
                logger.info("Error when parsing result link")
            logger.debug(e)
            return

        result_page_cnt = 0
        event_page_cnt = 0
        while result_page_cnt < result_page_limit and event_page_cnt < event_page_limit:
            logger.info(f"Processing result page: {result_page_cnt}")
            decks_copy = copy.deepcopy(decks)  # backup
            try:
                events = driver.find_elements(By.CLASS_NAME, "eventListItem")
                pbar = tqdm(events)
                for event in pbar:
                    pbar.set_description(f"Processing result page: {result_page_cnt}")
                    title = event.find_element(By.CLASS_NAME, "title")
                    if "シティリーグ" in title.text:
                        event_meta = get_event_meta(event)

                        t1 = time.time()
                        parse_event_to_deck(
                            event_meta["event_link"],
                            event_meta["num_players"],
                            decks,
                            skip_codes,
                            deck_page_limit,
                        )
                        t2 = time.time()
                        logger.debug(f"Event Time diff part1: {t2 - t1}")

                        event_page_cnt += 1

            except Exception as e:
                # Error handling:
                # - log exception
                # - skip this result page
                # - and restore decks
                if isinstance(e, WebDriverException):
                    logger.info("WebDriverException when parsing event link")
                    logger.info(
                        "This situation might cause by"
                        "unstable network connection,"
                        "please try to run the program again"
                    )
                else:
                    logger.info("Error when parsing event link")
                logger.debug(e)
                logger.debug(f"Processing result page: {result_page_cnt}")

                decks = copy.deepcopy(decks_copy)  # restore

            # nevigate to the next result page
            result_page_cnt += 1
            try:
                driver.find_element(By.CLASS_NAME, "btn.next").click()
                wait_loading_circle(driver)
            except Exception as e:
                if isinstance(e, TimeoutError):
                    logger.info("Wait for loading circle Timeout")
                elif isinstance(e, NoSuchElementException):
                    logger.info("Next event page not found")
                logger.debug(e)
                break


if __name__ == "__main__":
    t1 = time.time()
    pokemon_dict, tool_dict, supporter_dict, stadium_dict, energy_dict = parse_deck(
        deck_link="https://www.pokemon-card.com/deck/confirm.html/deckID/c8G888-na3SQ1-x8aDGc"
    )
    t2 = time.time()
    categories = find_categories(pokemon_dict, tool_dict, energy_dict)
    print("parse_deck():")
    print(f"category: {categories}")
    print("pokemon_dict")
    print(pokemon_dict)
    print("tool_dict")
    print(tool_dict)
    print("supporter_dict")
    print(supporter_dict)
    print("stadium_dict")
    print(stadium_dict)
    print("energy_dict")
    print(energy_dict)
    print(f"time diff: {t2-t1}")
    print("\n")

#     event_link = "https://players.pokemon-card.com/event/detail/45996/result"
#     num_players = 300
#     decks = {}
#     parse_event_to_deck(event_link, num_players, decks, [], num_pages=2)
#     print("parse_event_to_deck()")
#     print(decks)
#     print(decks.keys())
#     for k in decks.keys():
#         print(f"[{k}]: {len(decks[k])}")

#     import json
#     with open("test_parse_deck.json", 'w') as f:
#         json.dump(decks, f, ensure_ascii=False, indent=4)