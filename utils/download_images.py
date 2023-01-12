import argparse
import os
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

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

# Create image folder
IMG_FOLDER = Path(__file__).parent / "images"


def download_images(card_code_list, output_folder=IMG_FOLDER):
    # create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with webdriver.Chrome(options=chrome_options) as driver:
        pbar = tqdm(card_code_list)
        for card_code in pbar:
            pbar.set_description(f"Downloading: {card_code}")
            # Extract expansion symbol and collector number
            expansion_symbol, collector_number = card_code.split(" ")
            collector_number, total = collector_number.split("/")
            if collector_number > total:
                print(
                    f"{card_code}, collector_number > total, "
                    "please find a replaced card code "
                    "and save in mapping dictionary"
                )
                continue

            # Calculate page offset
            # 1 page has 20 cards at most
            collector_number = int(collector_number)
            offset = collector_number / 20 + 1
            url = (
                "https://asia.pokemon-card.com/tw/card-search/list/"
                f"?pageNo={offset}&expansionCodes={expansion_symbol}"
            )

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

            # Download image
            image_url = image_urls[offset]
            file_name = image_url.split("/")[-1]
            file_path = f"{output_folder}/{file_name}"
            if not os.path.exists(file_path):
                urllib.request.urlretrieve(image_url, file_path)
            else:
                print(f"{file_name} exists for {card_code}")


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
    download_images(card_code_list=args.code_list, folder=args.output_folder)


if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    print(t2 - t1)
