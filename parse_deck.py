from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--start-maximized");

def extract_card(cards):
    _dict = {}
    
    for c in cards[1:]:
        c = c.split(" ")
        if '（' in c[0]:
            loc = c[0].find('（')
            c[0] = c[0][:loc]
        _dict[c[0]] = c[1][:-1]
    
    return _dict


def parse_deck(deck_code: str):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.pokemon-card.com/deck/confirm.html/deckID/{deck_code}/")
    driver.find_element(By.ID, "deckView01").click()  # Click リスト表示 
    elems = driver.find_elements(By.CLASS_NAME, "Grid_item")
    
    pokemon_dict = {}  # {card_name: no.cards}
    tool_dict = {}
    supporter_dict = {}
    stage_dict = {}
    energy_dict = {}

    for e in elems:
        if "ポケモン" in e.text:
            cards = e.text.split('\n')
            for i in range(1, len(cards), 4):
                pokemon_dict[cards[i]] = cards[i+3][:-1]
        else:
            cards = e.text.split('\n')
            res = extract_card(cards)
            if "グッズ" in e.text:
                tool_dict = res
            elif "サポート" in e.text:
                supporter_dict = res
            elif "スタジアム" in e.text:
                stage_dict = res
            elif "エネルギー" in e.text:
                energy_dict = res

    driver.close()
    
    return pokemon_dict, tool_dict, supporter_dict, stage_dict, energy_dict


if __name__ == "__main__":
    pokemon_dict, tool_dict, supporter_dict, stage_dict, energy_dict = \
    parse_deck(deck_code = "cxxD8D-F0CeQo-8YxJ88")
    
    print("---")
    print("pokemon_dict"); print(pokemon_dict)
    print("tool_dict"); print(tool_dict)
    print("supporter_dict"); print(supporter_dict)
    print("stage_dict"); print(stage_dict)
    print("energy_dict"); print(energy_dict)
