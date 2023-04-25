import argparse
import json
import re
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


def is_alphanumeric(string):
    return bool(re.match("^[a-zA-Z0-9 /]+$", string))


def is_basic_energy(string):
    return bool(re.match("基本(草|炎|水|雷|超|闘|鋼|悪)エネルギー", string))


def format_for_blog(
    input_file_path,
    output_file_path,
    mapping_file_path,
    is_download_image=False,
    download_image_folder=DOWNLOAD_IMAGE_FOLDER,
    is_resize_image=False,
    resize_image_folder=None,
    embed_image_url=False,
    language="ch",
):
    if language not in ["ch", "jp"]:
        raise Exception(
            f"Language not supported: {language}, currently only support 'ch', 'jp'"
        )

    # Open mapping dictionary
    with open(mapping_file_path, "r") as f:
        mapping_dict = json.load(f)

    # Create the output file
    with open(output_file_path, "w") as f:
        f.write("# " + Path(input_file_path).stem + "\n")
        if language == "ch":
            f.write(":warning: 如果使用手機建議請橫置閱讀\n")
            f.write(":floppy_disk: [完整資料連結, 僅開放檢視權限](INPUT HERE)\n")
            f.write(
                ":flag-tw: [圖片皆取自於台灣寶可夢官網](https://asia.pokemon-card.com/tw/)\n"
            )
        else:
            pass  # TODO: jp
        f.write("###### tags: `PTCG` `日本上位構築`\n")

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
        num_rows_to_show = df_sheet["date"].isna().sum()
        end_row = START_ROW + num_rows_to_show
        idx_to_show = list(range(1, num_rows_to_show + 1))
        pick_rate_idx = idx_to_show[: len(idx_to_show) // 2]
        avg_num_use_idx = idx_to_show[len(idx_to_show) // 2 :]

        # print(pick_rate_idx)
        # print(avg_num_use_idx)

        # Extract the matrix of values from the
        # DataFrame within a specified range
        column_names = df_sheet.columns.to_numpy()[START_COL:]
        data = df_sheet.iloc[START_ROW:end_row, START_COL:end_col].values
        matrix = np.vstack([column_names, data])

        # Transpose the matrix using the T attribute of the numpy library
        transposed_matrix = matrix.T

        # Convert the transposed matrix to a list of strings with newlines
        strings = []
        pbar = tqdm(transposed_matrix)
        for row in pbar:
            # Embedded image block
            strings.append(
                '<div style="float: left; width: 50%;">'
            )  # column script
            card_name = row[0]
            try:
                card_name = card_name.split("\n")[-1]
                if is_basic_energy(card_name):
                    # For basic energy card
                    if embed_image_url:
                        image_url = mapping_dict[card_name]["image_url"]
                    else:
                        image_url = None
                else:
                    if is_alphanumeric(card_name):
                        # For pokemon cards
                        card_code = card_name
                    else:
                        # For other type of cards
                        jp_card_name = card_name
                        if jp_card_name not in mapping_dict:
                            raise ValueError
                        map_code_list = mapping_dict[jp_card_name]["code_list"]
                        if map_code_list:
                            card_code = map_code_list[0][0]
                        else:
                            card_code = None

                    if card_code:
                        card_code_list.append(card_code)

                    if embed_image_url:
                        image_url = extract_image_url(card_code)
                    else:
                        image_url = None
            except (ValueError, IndexError):
                print(card_name)
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
                # write card name
                if index == 0:
                    content = content.split("\n")
                    if len(content) == 3:
                        ch_card_name, jp_card_name, card_code = content
                    elif len(content) == 2:
                        ch_card_name, jp_card_name = content
                        card_code = ""
                    else:
                        ch_card_name, jp_card_name, card_code = (
                            "Error",
                            "Error",
                            "Error",
                        )

                    if language == "ch":
                        display_name = ch_card_name + " " + card_code
                    else:
                        display_name = jp_card_name + " " + card_code

                    strings.append(f"## {display_name}<br>")

                # write pick rate and diff of pick rate
                if index == pick_rate_idx[0]:
                    if language == "ch":
                        strings.append(f"採用率:\t**{content}**<br>")
                        strings.append("採用率每週變化:\n")
                    else:
                        pass  # TODO: jp
                if index in pick_rate_idx[1:]:
                    strings[-1] += f"{content} -> "

                # write avg pick num and diff of avg pick num
                if index == avg_num_use_idx[0]:
                    if language == "ch":
                        strings.append(f"\n平均採用張數:\t**{content}**<br>")
                        strings.append("平均採用張數每週變化:\n")
                    else:
                        pass  # TODO: jp
                if index in avg_num_use_idx[1:]:
                    strings[-1] += f"{content} -> "
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
    parser.add_argument(
        "--embed_image_url",
        "-e",
        action="store_true",
        help="Embed image url in output file",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="ch",
        help="Chose language of this blog, support: [ch, jp]",
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
        embed_image_url=args.embed_image_url,
        language=args.language,
    )


if __name__ == "__main__":
    main()
