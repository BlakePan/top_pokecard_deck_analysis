import argparse
import os
import time
import urllib.request
from pathlib import Path
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from tqdm import tqdm

from .chrome_options import chrome_options
from .translator import map_card_name

# Create image folder
IMG_FOLDER = Path(__file__).parent / "images"

# For jp site
EXP_SYMBOL_MAPPING = {
    "SV-P": "SV-P",
    "SV2P": 879,
    "SV2D": 880,
    "SVC": 878,
    "SV1a": 877,
    "SV1S": 870,
    "SV1V": 871,
    "SVAM": 872,
    "SVAL": 873,
    "SVAW": 874,
    "SVB": 875,
    "S12a": 869,
    "SO": 868,
    "S12": 867,
    "S11a": 866,
    "SP6": 865,
    "S11": 862,
    "SPZ": 863,
    "SPD": 864,
    "S10b": 861,
    "S10a": 859,
    "S10D": 856,
    "S10P": 857,
    "S9a": 853,
    "SLL": 854,
    "SLD": 855,
    "SN": 852,
    "SK": 849,
    "S9": 851,
    "SI": 850,
    "S8b": 748,
    "SJ": 747,
    "S8a": 746,
    "S8a-G": 860,
    "S8": 745,
    "SP5": 744,
    "S7R": 740,
    "SH": 738,
    "SP4": 737,
    "S6a": 736,
    "SGI": 735,
    "SGG": 734,
    "SP3": 733,
    "S6K": 732,
    "S6H": 731,
    "S5a": 730,
    "SF": 729,
    "S5R": 728,
    "S5I": 727,
    "SEF": 725,
    "SEK": 724,
}

PAGE_CARDNUM_MAX = {
    "ch": 20,
    "jp": 39,
}


def extract_image_url(card_code: str, language: str = "ch") -> str:
    if not isinstance(card_code, str):
        raise ValueError

    # Extract expansion symbol and collector number
    expansion_symbol, collector_number = card_code.split(" ")
    collector_number, total = collector_number.split("/")
    if collector_number > total:
        raise ValueError(
            f"{card_code}, collector_number > total, "
            "please find a replaced card code "
            "and save in mapping dictionary"
        )

    # Calculate page offset
    # for ch 1 page has 20 cards at most, for jp 39 cards at most
    collector_number = int(collector_number)

    # Ch workaround
    if language == "ch":
        # S8b has v-union
        if expansion_symbol == "S8b" and collector_number >= 60:
            collector_number -= 3
        # S7D, the first card is in wrong place XD
        if expansion_symbol == "S7D":
            if collector_number == 56:
                collector_number = 1
            else:
                collector_number += 1

    # URL
    offset = (collector_number - 1) // PAGE_CARDNUM_MAX[language] + 1
    if language == "ch":
        url = (
            "https://asia.pokemon-card.com/tw/card-search/list/"
            f"?pageNo={offset}&expansionCodes={expansion_symbol}"
        )
        with webdriver.Chrome(options=chrome_options) as driver:
            # Init driver
            driver.implicitly_wait(2)  # seconds
            driver.get(url)

            # Extract image url
            card_list = driver.find_element(
                By.CLASS_NAME, "rightColumn"
            ).find_elements(By.CLASS_NAME, "card")
            image_urls = [
                card.find_element(
                    By.CSS_SELECTOR, "li.card img.lazy"
                ).get_attribute("data-original")
                for card in card_list
            ]
            # Calculate matrix offset
            offset = (collector_number - 1) % PAGE_CARDNUM_MAX[language]

            # Get image
            image_url = image_urls[offset]
    else:
        jp_card_name = map_card_name(card_code, "jp")
        pg_code = EXP_SYMBOL_MAPPING[expansion_symbol]
        url = (
            "https://www.pokemon-card.com/card-search/index.php?"
            "keyword=&se_ta=&regulation_sidebar_form=all&"
            f"pg={pg_code}&illust=&sm_and_keyword=true"
        )
        # print("https://www.pokemon-card.com/card-search/index.php?keyword=&se_ta=&regulation_sidebar_form=all&pg=877&illust=&sm_and_keyword=true")
        # print(url)
        with webdriver.Chrome(options=chrome_options) as driver:
            # Init driver
            driver.implicitly_wait(2)  # seconds
            driver.get(url)

            # Get total page count
            number_element = driver.find_element(By.CLASS_NAME, "result-tag")
            number_element = number_element.find_element(
                By.CSS_SELECTOR, "div.result-tag > span:first-child"
            )
            total_page_count = int(number_element.text)
            # print(f"total_page_count: {total_page_count}")

        # Extract image url
        image_url = None
        for page_offset in range(
            1, total_page_count + 1
        ):  # TODO: find a way for not looping
            page_url = (
                "https://www.pokemon-card.com/card-search/index.php?"
                "keyword=&se_ta=&regulation_sidebar_form=all&"
                f"pg={pg_code}&illust=&sm_and_keyword=true&page={page_offset}"
            )

            if image_url is not None:
                break

            try:
                with webdriver.Chrome(options=chrome_options) as driver:
                    # Init driver
                    driver.implicitly_wait(2)  # seconds
                    driver.get(page_url)

                    card_list = driver.find_element(
                        By.CLASS_NAME, "SearchResultList-box"
                    ).find_elements(By.CLASS_NAME, "List_item")

                    for card in card_list:
                        if (
                            card.find_element(
                                By.CSS_SELECTOR, "img"
                            ).get_attribute("alt")
                            == jp_card_name
                        ):
                            image_url = (
                                "https://www.pokemon-card.com/"
                                + card.find_element(
                                    By.CSS_SELECTOR, "img"
                                ).get_attribute("data-src")
                            )
                            break
            except NoSuchElementException:
                # print("bypass..., maybe in the next page")
                pass

    return image_url


def download_images(
    card_code_list,
    output_folder: str = IMG_FOLDER,
    specified_names: List = None,
    exists_ok: bool = False,
    language: str = "ch",
):
    # create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # check specified_names
    specified_names = specified_names if specified_names else []
    is_specified_names_ok = isinstance(specified_names, list)
    if is_specified_names_ok:
        is_specified_names_ok = len(card_code_list) == len(specified_names)
        for name in specified_names:
            if not isinstance(name, str):
                is_specified_names_ok = False
                break

    pbar = tqdm(card_code_list)
    for index, card_code in enumerate(pbar):
        try:
            pbar.set_description(f"Downloading: {card_code}")
            image_url = extract_image_url(card_code, language=language)
            if is_specified_names_ok:
                file_name = specified_names[index]
            else:
                file_name = image_url.split("/")[-1]
            file_path = f"{output_folder}/{file_name}"
            if exists_ok or not os.path.exists(file_path):
                urllib.request.urlretrieve(image_url, file_path)
            else:
                print(f"{file_name} exists for {card_code}")
        except Exception as e:
            print(f"{card_code} has error, skip downloading")
            print(str(e))
            continue


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--code_list",
        nargs="+",
        type=str,
        required=True,
        help="list of card codes for downloading images. "
        'e.g. -c "S12a 001/100", "S7R 042/0671"',
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        required=False,
        default=IMG_FOLDER,
        help="path to the folder where the images will be saved",
    )
    parser.add_argument(
        "-l",
        "--language",
        required=False,
        default="ch",
        help="download 'ch' or 'jp' card",
    )
    args = parser.parse_args()

    # download the images
    download_images(
        card_code_list=args.code_list,
        output_folder=args.output_folder,
        language=args.language,
    )


if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    print(t2 - t1)
