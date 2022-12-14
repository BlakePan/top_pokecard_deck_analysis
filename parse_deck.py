from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tqdm import tqdm
import re
import unicodedata

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--start-maximized")

# https://blog.csdn.net/sxf1061700625/article/details/124263680
# disable images
chrome_options.add_argument('blink-settings=imagesEnabled=false')
chrome_options.add_argument('--disable-images')
# disable javascripts
chrome_options.add_argument("--disable-javascript")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-java')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--mute-audio')
chrome_options.add_argument('--single-process')
chrome_options.add_argument("--disable-blink-features")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument('--incognito')


def full2half(c: str) -> str:
    return unicodedata.normalize("NFKC", c)


def wait_loading_circle(driver, timeout: int = 20):
    WebDriverWait(driver, 20).until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='sk-circle-container']")))


def extract_card(cards):
    _dict = {}
    
    for c in cards[1:]:
        c = c.split(" ")
        loc = -1
        if '（' in c[0]:
            loc = c[0].find('（')
        elif '(' in c[0]:
            loc = c[0].find('(')
        c[0] = c[0][:loc] if loc != -1 else c[0]
        _dict[c[0]] = int(c[-1][:-1])
    
    return _dict


def find_category(all_categories: dict, pokemon_dict: dict) -> str:
    # identify this deck belongs to which category (TODO: need more rules)
    category = "others"
    poke_cards = pokemon_dict.keys()

    for c in all_categories["simple"]:
        if c in poke_cards:
            category = c
            break

    if category != "others":
        pass
    else:
        if "ゾロア" in poke_cards:
            if "ヒスイ ウインディ" in poke_cards:
                category = "ゾロア ウインディ"
            else:
                category = "ゾロア"
        elif "レジドラゴVSTAR" in poke_cards:
            if "アルセウスVSTAR" in poke_cards:
                category = "アルレジドラゴVSTAR"
            else:
                category = "レジドラゴVSTAR"
        elif "ギラティナVSTAR" in poke_cards:
            if "キュワワー" in poke_cards:
                category = "LOST ギラティナVSTAR"
            else:
                category = "Other ギラティナVSTAR"
        elif "キュワワー" in poke_cards:
            if "フリーザー" in poke_cards and "ヤミラミ" not in poke_cards:
                category = "LTB ウッウ"
            elif "かがやくリザードン" in poke_cards:
                category = "LTB リザードン" if "ヤミラミ" not in poke_cards else "LTB ヤミラミ リザードン"
            elif "かがやくゲッコウガ" in poke_cards:
                category = "LTB"
            else:
                category = "Other Lost"
        elif "レジギガス" in poke_cards and \
                "レジドラゴ" in poke_cards and \
                "レジスチル" in poke_cards and \
                "レジロック" in poke_cards and \
                "レジアイス" in poke_cards and \
                "レジエレキ" in poke_cards:
            category = "レジ"
        elif "アルセウスVSTAR" in poke_cards:
            if "メッソン" in poke_cards:
                category = "アルセウス裏工作"
            elif "ジュラルドンVMAX" in poke_cards:
                category = "アル ジュラルドン"
            elif "そらをとぶピカチュウVMAX" in poke_cards:
                category = "アル そらをとぶピカチュウ"

    return category


def reassign_category(decks: dict, all_categories: dict) -> dict:
    """
    """
    new_decks = {}

    for k in decks.keys():
        for d in decks[k]:
            category = find_category(all_categories, d["pokemons"])
            if category not in new_decks:
                new_decks[category] = []

            new_decks[category].append(d)

    return new_decks


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


def parse_event_to_deck(event_link: str,
                        num_people: int,
                        decks: dict,
                        all_categories: dict,
                        skip_codes: list,
                        num_pages: int = 1):
    """
    num_pages < 0: parse all pages
    """
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10) # seconds
    driver.get(event_link)
    date_str = driver.find_element(By.CLASS_NAME, "date-day").text

    while num_pages:
        deck_elems = driver.find_elements(By.CLASS_NAME, "c-rankTable-row")
        for deck_idx, deck_elem in enumerate(deck_elems):
            try:
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
            except Exception as e:
                print(e)
                print(event_link)
                print(f"skip deck no. {deck_idx}")

        # nevigate to the next page
        try:
            num_pages -= 1
            if num_pages:
                driver.find_element(By.CLASS_NAME, "btn.next").click()
                wait_loading_circle(driver)
        except Exception as e:
            print(e)
            print("next deck page not found")
            break

    driver.close()


def parse_events_from_official(decks: dict, all_categories: dict,
                               skip_codes: list = None, page_limit: int = 10, event_limit: int = 100):
    skip_codes = [] if skip_codes is None else skip_codes

    # parse CL event links from official website
    url = "https://players.pokemon-card.com/event/result/list"
    driver = webdriver.Chrome(options=chrome_options)  # options=chrome_options
    driver.implicitly_wait(10) # seconds
    driver.get(url)

    page_cnt = 0
    event_cnt = 0
    while 1:
        events = driver.find_elements(By.CLASS_NAME, "eventListItem")
        for event in tqdm(events):
            title = event.find_element(By.CLASS_NAME, "title")
            if "シティリーグ" in title.text:
                num_people_str = event.find_element(By.CLASS_NAME, "capacity").text
                num_people = re.findall(r'\d+', num_people_str)
                num_people = int(num_people[0]) if len(num_people) == 1 else None
                event_link = event.get_attribute("href")
                parse_event_to_deck(event_link, num_people, decks, all_categories, skip_codes)
                event_cnt += 1
        page_cnt += 1

        if page_cnt >= page_limit or event_cnt >= event_limit:
            break

        # nevigate to the next page
        try:
            driver.find_element(By.CLASS_NAME, "btn.next").click()
        except Exception as e:
            print(e)
            print("next event page not found")
            break
        wait_loading_circle(driver)

    driver.close()


if __name__ == "__main__":
    all_categories = {"simple": ["ルギアVSTAR", "ミュウVMAX", "ジュラルドンVMAX", "ムゲンダイナVMAX"]}

    pokemon_dict, tool_dict, supporter_dict, stage_dict, energy_dict = \
        parse_deck(deck_link = "https://www.pokemon-card.com/deck/confirm.html/deckID/gNNgLn-iz2ItL-QngnnL")
#         parse_deck(deck_code = "gngLgL-7AWHa3-LNgNnn")
    category = find_category(all_categories, pokemon_dict)
    print("parse_deck():")
    print(f"category: {category}")
    print("pokemon_dict"); print(pokemon_dict)
    print("tool_dict"); print(tool_dict)
    print("supporter_dict"); print(supporter_dict)
    print("stage_dict"); print(stage_dict)
    print("energy_dict"); print(energy_dict)
    print("\n")

#     event_link = "https://players.pokemon-card.com/event/detail/45996/result"
#     num_people = 300
#     decks = {}
#     parse_event_to_deck(event_link, num_people, decks, all_categories, [], num_pages=2)
#     print("parse_event_to_deck()")
#     print(decks)
#     print(decks.keys())
#     for k in decks.keys():
#         print(f"[{k}]: {len(decks[k])}")

#     import json
#     with open("test_parse_deck.json", 'w') as f:
#         json.dump(decks, f, ensure_ascii=False, indent=4)
