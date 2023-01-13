import argparse
import copy
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

# TODO: workaround for importing
sys.path.append(str(Path.cwd()))

from deck_crawler.utils.chrome_options import chrome_options
from deck_crawler.utils.font import full2half

URL_PATTERN = "https://www.pokemon-card.com"
BASIC_ENERGE_PATTERN = "基本.*エネルギー"


def get_card_code(driver) -> str:
    # Find card code element
    cardcode_element = driver.find_element(By.CLASS_NAME, "subtext.Text-fjalla")

    # Extract expansion symbol
    expansion_symbol = cardcode_element.find_element(
        By.CLASS_NAME, "img-regulation"
    ).get_attribute("alt")

    # Extract collector number
    collector_number = cardcode_element.text
    collector_number = full2half(collector_number)
    collector_number = collector_number.replace(" ", "")

    return f"{expansion_symbol} {collector_number}"


def update_mapping_dict(
    mapping_file_path,
    is_debug=False,
):
    # Open mapping dict file
    with open(mapping_file_path, "r") as f:
        mapping_dict = json.load(f)
    temp_dict = copy.deepcopy(mapping_dict)

    # Collect card names that needs to be update
    card_names = []
    for card_name, card_info in mapping_dict.items():
        if card_info["code_list"]:
            continue
        if re.search(BASIC_ENERGE_PATTERN, card_name):
            continue
        card_names.append(card_name)
    print(card_names)
    print("===========")

    pbar = tqdm(card_names)
    for card_name in pbar:
        pbar.set_description(f"Updating: {card_name}")
        with webdriver.Chrome(options=chrome_options) as driver:
            # Get url by putting card name in keyword
            encoded_string = urllib.parse.quote(card_name)
            url = f"https://www.pokemon-card.com/card-search/index.php?keyword={encoded_string}"

            # Init web driver
            driver.implicitly_wait(2)  # seconds
            driver.get(url)

            # Locate to the first link in image matrix
            result_area = driver.find_element(By.ID, "SearchResultListArea")

            # Locate image element and click on it
            # TODO: need to optimize, some card code is not in ch database
            item_element = result_area.find_element(By.CLASS_NAME, "List_item")
            img_element = item_element.find_element(By.ID, "card-show-id0")
            img_element.click()

            # Switch to pop-up window
            parent_window = driver.current_window_handle
            child_windows = driver.window_handles
            for child_window in child_windows:
                if child_window != parent_window:
                    driver.switch_to.window(child_window)
                    break
            time.sleep(0.1)

            # Get card code
            card_code = get_card_code(driver)

            # Update the mapping dictionary
            code_list = temp_dict[card_name]["code_list"]
            if not code_list:
                temp_dict[card_name]["code_list"] = [[]]
            temp_dict[card_name]["code_list"][0].append(card_code)

    # Update the json
    if is_debug:
        mapping_file_path = mapping_file_path + ".debug.json"
    with open(mapping_file_path, "w") as f:
        json.dump(temp_dict, f, ensure_ascii=False, indent=4)


def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mapping_file_path",
        "-m",
        default=None,
        help="Path to the mapping file",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Debug mode",
    )

    args = parser.parse_args()

    update_mapping_dict(
        mapping_file_path=args.mapping_file_path,
        is_debug=args.debug,
    )


if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    print(t2 - t1)
