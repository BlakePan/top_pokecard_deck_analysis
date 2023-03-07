import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

# TODO: workaround for importing
sys.path.append(str(Path.cwd()))

from deck_crawler.utils.download_images import (
    download_images,
    extract_image_url,
)
from deck_crawler.utils.resize_images import resize_images
from deck_crawler.utils.translator import translate_ch_to_jp

# Set the range of the matrix
START_ROW = 0
END_ROW = 2
START_COL = 5
SHEET_NAMES = [
    ("pokemons", "寶可夢"),
    ("tools", "物品"),
    ("supporters", "支援者"),
    ("stadiums", "競技場"),
    ("energies", "能量"),
]

DOWNLOAD_IMAGE_FOLDER = Path(__file__).parent / "download_imgs"
MAPPING_FILE_PATH = (
    Path(__file__).parent.parent / "deck_crawler/assets/card_mapping.json"
)


def format_for_blog(
    input_file_path,
    output_file_path,
    mapping_file_path,
    is_download_image=False,
    download_image_folder=DOWNLOAD_IMAGE_FOLDER,
    is_resize_image=False,
    resize_image_folder=None,
):
    # Open mapping dictionary
    with open(mapping_file_path, "r") as f:
        mapping_dict = json.load(f)

    # Create the output file
    with open(output_file_path, "w") as f:
        f.write("# " + Path(input_file_path).stem + "\n\n")

    # Init list for containning codes
    card_code_list = []

    # Loop through each sheet in the file
    for sheet_index, sheet_name in enumerate(SHEET_NAMES):
        sheet_name_eng, sheet_name_ch = sheet_name

        # Read the sheet data from the Excel file
        df_sheet = pd.read_excel(input_file_path, sheet_name=sheet_name_eng)

        # Determine the dimensions of the matrix
        _, num_cols = df_sheet.shape
        end_col = num_cols

        # Extract the matrix of values from the
        # DataFrame within a specified range
        column_names = df_sheet.columns.to_numpy()[START_COL:]
        data = df_sheet.iloc[START_ROW:END_ROW, START_COL:end_col].values
        matrix = np.vstack([column_names, data])

        # Transpose the matrix using the T attribute of the numpy library
        transposed_matrix = matrix.T

        # Convert the transposed matrix to a list of strings with newlines
        strings = []
        pbar = tqdm(transposed_matrix)
        for row in pbar:
            if sheet_name_ch != "能量":
                # Embedded image block
                strings.append(
                    '<div style="float: left; width: 50%;">'
                )  # column script
                try:
                    card_name = row[0]
                    if "\n" in card_name:
                        # For pokemon cards
                        card_code = card_name.split("\n")[-1]
                        card_code_list.append(card_code)
                    else:
                        # For other type of cards
                        jp_card_name = translate_ch_to_jp(card_name)
                        if jp_card_name not in mapping_dict:
                            raise ValueError
                        map_code_list = mapping_dict[jp_card_name]["code_list"]
                        if map_code_list:
                            card_code = map_code_list[0][0]
                            card_code_list.append(card_code)
                        else:
                            card_code = None
                    image_url = extract_image_url(card_code)
                except ValueError:
                    image_url = None

                if image_url:
                    strings.append(
                        f'<img src="{image_url}" alt="" width="300" height="400">'
                    )
                else:
                    strings.append("<br>")
                strings.append("</div>")

            # Statistic data block
            strings.append(
                '<div style="float: left; width: 50%;">\n'
            )  # column script
            for index, content in enumerate(row):
                if index == 0:
                    strings.append(f"{content}<br>")  # write card name
                elif index == 1:
                    strings.append(f"採用率:\t{content}<br>")
                elif index == 2:
                    strings.append(f"平均採用張數:\t{content}<br>")
            strings.append("<br><br><br><br><br><br><br><br><br><br><br>")
            strings.append("</div>")
            strings.append("")

        # Output the strings to a file
        with open(output_file_path, "a") as f:
            f.write("# " + sheet_name_ch + "\n\n")
            for s in strings:
                f.write(s + "\n")

    # Download images
    if is_download_image:
        download_images(card_code_list, download_image_folder)

    # Resize images
    if is_resize_image:
        if not resize_image_folder:
            resize_image_folder = Path(output_file_path).parent / "resized_imgs"
        resize_images(download_image_folder, resize_image_folder)


def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path",
        "-i",
        required=True,
        help="Path to the input file, current supports: Excel",
    )
    parser.add_argument(
        "--output_path",
        "-o",
        default="output.md",
        help="Path to the output file",
    )
    parser.add_argument(
        "--mapping_file_path",
        "-m",
        default=MAPPING_FILE_PATH,
        help="Path to the mapping file",
    )
    parser.add_argument(
        "--download_images", "-d", action="store_true", help="Download images"
    )
    parser.add_argument(
        "--download_folder",
        "-df",
        default=DOWNLOAD_IMAGE_FOLDER,
        help="Path for download images",
    )
    parser.add_argument(
        "--resize_images",
        "-rs",
        action="store_true",
        help="Resize downloaded images",
    )
    parser.add_argument(
        "--resize_folder",
        "-rsf",
        default=None,
        help="Path for output resized images",
    )

    args = parser.parse_args()

    format_for_blog(
        input_file_path=args.input_path,
        output_file_path=args.output_path,
        mapping_file_path=args.mapping_file_path,
        is_download_image=args.download_images,
        is_resize_image=args.resize_images,
        download_image_folder=args.download_folder,
        resize_image_folder=args.resize_folder,
    )


if __name__ == "__main__":
    main()
