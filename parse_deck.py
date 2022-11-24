from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--start-maximized")

def extract_card(cards):
    _dict = {}
    
    for c in cards[1:]:
        c = c.split(" ")
        if '（' in c[0]:
            loc = c[0].find('（')
            c[0] = c[0][:loc]
        _dict[c[0]] = int(c[-1][:-1])
    
    return _dict


def find_category(all_categories, pokemon_dict):
    # identify this deck belongs to which category (TODO: need more rules)
    category = "others"
    for c in all_categories[:-1]:
        if c in pokemon_dict.keys():
            category = c

    return category


def parse_deck(deck_code: str = None, deck_link: str = None):
    if not deck_code and not deck_link:
        return

    url = deck_link if deck_link else f"https://www.pokemon-card.com/deck/confirm.html/deckID/{deck_code}/"
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10) # seconds

    driver.get(url)
    driver.find_element(By.ID, "deckView01").click()  # Click リスト表示 
    elems = driver.find_element(By.ID, "cardListView").find_elements(By.CLASS_NAME, "Grid_item")
    
    pokemon_dict = {}  # {card_name: no.cards}
    tool_dict = {}
    supporter_dict = {}
    stage_dict = {}
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
            cards = e.text.split('\n')
            for i in range(1, len(cards), 4):
                pokemon_dict[cards[i]] = int(cards[i+3][:-1])
        else:
            """
            example:

            グッズ (19)
            クイックボール 3枚
            """
            cards = e.text.split('\n')
            res = extract_card(cards)
            if "グッズ (" in e.text:
                tool_dict = res
            elif "サポート (" in e.text:
                supporter_dict = res
            elif "スタジアム (" in e.text:
                stage_dict = res
            elif "エネルギー (" in e.text:
                energy_dict = res

    driver.close()
    
    return pokemon_dict, tool_dict, supporter_dict, stage_dict, energy_dict


def parse_event_to_deck(event_link: str, num_people: int, decks: dict, all_categories: list, skip_codes: list = None):
    skip_codes = [] if skip_codes is None else skip_codes
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10) # seconds
    driver.get(event_link)
    date_str = driver.find_element(By.CLASS_NAME, "date-day").text
    deck_elems = driver.find_elements(By.CLASS_NAME, "c-rankTable-row")

    for deck_elem in deck_elems:
        deck_link = deck_elem.find_element(By.CLASS_NAME, "deck").find_element(By.TAG_NAME, "a").get_property("href")
        deck_code = deck_link.split("/")[-1]
        if deck_code in skip_codes:
            continue

        pokemon_dict, tool_dict, supporter_dict, stage_dict, energy_dict = parse_deck(deck_link = deck_link)
        category = find_category(all_categories, pokemon_dict)
        rank = int(deck_elem.find_element(By.TAG_NAME, "td").get_attribute("class").split("-")[-1])

        if category not in decks:
            decks[category] = []

        decks[category].append(
            {
                "deck_link": deck_link,
                "deck_code": deck_code,
                "pokemons": pokemon_dict,
                "tools": tool_dict,
                "supporters": supporter_dict,
                "stages": stage_dict,
                "energies": energy_dict,
                "rank": rank,
                "num_people": num_people,
                "date": date_str
            }
        )

    driver.close()


if __name__ == "__main__":
    pokemon_dict, tool_dict, supporter_dict, stage_dict, energy_dict = \
    parse_deck(deck_code = "pyyypy-FHfMje-MypyyM")
#     parse_deck(deck_link = "https://www.pokemon-card.com/deck/confirm.html/deckID/gngLgL-7AWHa3-LNgNnn")
    print("parse_deck():")
    print("pokemon_dict"); print(pokemon_dict)
    print("tool_dict"); print(tool_dict)
    print("supporter_dict"); print(supporter_dict)
    print("stage_dict"); print(stage_dict)
    print("energy_dict"); print(energy_dict)
    print("\n")

#     event_link = "https://players.pokemon-card.com/event/detail/31798/result"
#     num_people = 32
#     all_categories = ["ルギアVSTAR", "ミュウVMAX", "ジュラルドンVMAX", "others"]
#     decks = {}
#     parse_event_to_deck(event_link, num_people, decks, all_categories)
#     print("parse_event_to_deck()")
#     print(decks)
