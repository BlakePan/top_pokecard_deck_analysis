import concurrent.futures
import logging
import os
import re
import threading
import time
import unicodedata

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from deck_category_helper import find_category

# Set up logging to a file
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=f"logs/{os.path.basename(__file__)}.log",  # specify the log file name
    filemode="w",
)  # specify that the log file should be overwritten each time the script is run
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
    return unicodedata.normalize("NFKC", c)


def wait_loading_circle(driver, timeout: int = 20):
    WebDriverWait(driver, 20).until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//div[@class='sk-circle-container']")
        )
    )


def extract_card(cards):
    _dict = {}

    for c in cards[1:]:
        c = c.split(" ")
        loc = -1
        if "（" in c[0]:
            loc = c[0].find("（")
        elif "(" in c[0]:
            loc = c[0].find("(")
        c[0] = c[0][:loc] if loc != -1 else c[0]
        _dict[c[0]] = int(c[-1][:-1])

    return _dict


def reassign_category(decks: dict) -> dict:
    """ """
    new_decks = {}

    for k in decks.keys():
        for d in decks[k]:
            category = find_category(d["pokemons"], d["tools"], d["energies"])
            if category not in new_decks:
                new_decks[category] = []

            new_decks[category].append(d)

    return new_decks


def parse_deck(deck_code: str = None, deck_link: str = None):
    if not deck_code and not deck_link:
        return

    url = (
        deck_link
        if deck_link
        else f"https://www.pokemon-card.com/deck/confirm.html/deckID/{deck_code}/"
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(2)  # seconds

    driver.get(url)
    driver.find_element(By.ID, "deckView01").click()  # Click リスト表示
    elems = driver.find_element(By.ID, "cardListView").find_elements(
        By.CLASS_NAME, "Grid_item"
    )

    pokemon_dict = {}  # {card_name: no.cards}
    tool_dict = {}
    supporter_dict = {}
    stadium_dict = {}
    energy_dict = {}

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

    driver.close()

    return pokemon_dict, tool_dict, supporter_dict, stadium_dict, energy_dict


def crawl_pages(deck_metas):
    # Create the shared dictionary
    results = {}
    lock = threading.Lock()

    def crawl_page(deck_meta):
        url = deck_meta["url"]
        deck_code = deck_meta["deck_code"]
        rank = deck_meta["rank"]
        num_people = deck_meta["num_people"]
        date = deck_meta["date"]

        t1 = time.time()
        pokemon_dict, tool_dict, supporter_dict, stadium_dict, energy_dict = parse_deck(
            deck_link=url
        )
        t2 = time.time()
        logger.debug(f"parse_deck Time diff part1: {t2-t1}")

        category = find_category(pokemon_dict, tool_dict, energy_dict)

        with lock:
            if category not in results:
                results[category] = []

            results[category].append(
                {
                    "deck_link": url,
                    "deck_code": deck_code,
                    "pokemons": pokemon_dict,
                    "tools": tool_dict,
                    "supporters": supporter_dict,
                    "stadiums": stadium_dict,
                    "energies": energy_dict,
                    "rank": rank,
                    "num_people": num_people,
                    "date": date,
                }
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Create a task for each deck
        threads = []
        for deck_meta in deck_metas:
            task = executor.submit(crawl_page, deck_meta)
            threads.append(task)

        # Wait for all tasks to complete
        concurrent.futures.wait(threads)

    return results


def parse_event_to_deck(
    event_link: str,
    num_people: int,
    decks: dict,
    skip_codes: list,
    num_pages: int = 1,
):
    """
    num_pages < 0: parse all pages
    """
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(2)  # seconds
    driver.get(event_link)
    date_str = driver.find_element(By.CLASS_NAME, "date-day").text

    t1 = time.time()
    deck_metas = []
    while num_pages:
        # Collect metadata of available decks
        deck_elems = driver.find_elements(By.CLASS_NAME, "c-rankTable-row")
        for deck_idx, deck_elem in enumerate(deck_elems):
            try:
                url = (
                    deck_elem.find_element(By.CLASS_NAME, "deck")
                    .find_element(By.TAG_NAME, "a")
                    .get_property("href")
                )

                deck_code = url.split("/")[-1]
                if deck_code in skip_codes:
                    continue

                rank = int(
                    deck_elem.find_element(By.TAG_NAME, "td")
                    .get_attribute("class")
                    .split("-")[-1]
                )

                deck_metas.append(
                    {
                        "url": url,
                        "deck_code": deck_code,
                        "rank": rank,
                        "num_people": num_people,
                        "date": date_str,
                    }
                )
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
            logger.debug(e)
            logger.debug(event_link)
            logger.debug("next deck page not found")
            break
    t2 = time.time()
    logger.debug(f"Page Time diff part1: {t2-t1}")

    # wait for results
    logger.debug(deck_metas)
    t1 = time.time()
    results = crawl_pages(deck_metas)
    t2 = time.time()
    logger.debug(f"Page Time diff part2: {t2-t1}")

    # update crawl results to decks
    for category in results:
        if category not in decks:
            decks[category] = []
        decks[category] += results[category]

    driver.close()


def parse_events_from_official(
    decks: dict,
    skip_codes: list = None,
    page_limit: int = 10,
    event_limit: int = 100,
    num_page_in_event: int = 1,
):
    skip_codes = [] if skip_codes is None else skip_codes

    # parse CL event links from official website
    url = "https://players.pokemon-card.com/event/result/list"
    driver = webdriver.Chrome(options=chrome_options)  # options=chrome_options
    driver.implicitly_wait(2)  # seconds
    driver.get(url)

    page_cnt = 0
    event_cnt = 0
    while 1:
        events = driver.find_elements(By.CLASS_NAME, "eventListItem")
        pbar = tqdm(events)
        for event in pbar:
            pbar.set_description(f"Processing result page: {page_cnt}")
            title = event.find_element(By.CLASS_NAME, "title")
            if "シティリーグ" in title.text:
                t1 = time.time()

                num_people_str = event.find_element(By.CLASS_NAME, "capacity").text
                num_people = re.findall(r"\d+", num_people_str)
                num_people = int(num_people[0]) if len(num_people) == 1 else None
                event_link = event.get_attribute("href")
                logger.debug(f"event_link: {event_link}")

                t2 = time.time()

                parse_event_to_deck(
                    event_link,
                    num_people,
                    decks,
                    skip_codes,
                    num_page_in_event,
                )

                t3 = time.time()
                logger.debug(f"Event Time diff part1: {t2 - t1}")
                logger.debug(f"Event Time diff part2: {t3 - t2}")

                event_cnt += 1
        page_cnt += 1

        if page_cnt >= page_limit or event_cnt >= event_limit:
            break

        # nevigate to the next page
        try:
            driver.find_element(By.CLASS_NAME, "btn.next").click()
        except Exception as e:
            logger.debug(e)
            logger.debug("next event page not found")
            break
        wait_loading_circle(driver)

    driver.close()


if __name__ == "__main__":
    t1 = time.time()
    pokemon_dict, tool_dict, supporter_dict, stadium_dict, energy_dict = parse_deck(
        deck_link="https://www.pokemon-card.com/deck/confirm.html/deckID/c8G888-na3SQ1-x8aDGc"
    )
    t2 = time.time()
    category = find_category(pokemon_dict, tool_dict, energy_dict)
    print("parse_deck():")
    print(f"category: {category}")
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
#     num_people = 300
#     decks = {}
#     parse_event_to_deck(event_link, num_people, decks, [], num_pages=2)
#     print("parse_event_to_deck()")
#     print(decks)
#     print(decks.keys())
#     for k in decks.keys():
#         print(f"[{k}]: {len(decks[k])}")

#     import json
#     with open("test_parse_deck.json", 'w') as f:
#         json.dump(decks, f, ensure_ascii=False, indent=4)
