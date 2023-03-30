import argparse
import os
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

from .chrome_options import chrome_options

# Create image folder
IMG_FOLDER = Path(__file__).parent / "images"


def extract_image_url(card_code: str) -> str:
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
    # 1 page has 20 cards at most
    collector_number = int(collector_number)

    # special cases
    # s8b has v-union
    if expansion_symbol == "S8b" and collector_number >= 60:
        collector_number -= 3

    offset = (collector_number - 1) / 20 + 1
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
    offset = (collector_number - 1) % 20

    # Get image
    image_url = image_urls[offset]

    return image_url


def download_images(card_code_list, output_folder=IMG_FOLDER):
    # create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pbar = tqdm(card_code_list)
    for card_code in pbar:
        try:
            pbar.set_description(f"Downloading: {card_code}")
            image_url = extract_image_url(card_code)
            file_name = image_url.split("/")[-1]
            file_path = f"{output_folder}/{file_name}"
            if not os.path.exists(file_path):
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
    args = parser.parse_args()

    # download the images
    download_images(
        card_code_list=args.code_list, output_folder=args.output_folder
    )


if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    print(t2 - t1)
