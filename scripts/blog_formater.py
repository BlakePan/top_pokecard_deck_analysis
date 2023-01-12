import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# TODO: workaround for importing
sys.path.append(str(Path.cwd()))

from utils.download_images import download_images
from utils.resize_images import resize_images

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
RESIZE_IMAGE_FOLDER = Path(__file__).parent / "resized_imgs"


def format_for_blog(
    input_file_path,
    output_file_path,
    is_download_image=False,
    download_image_folder=DOWNLOAD_IMAGE_FOLDER,
    is_resize_image=False,
    resize_image_folder=RESIZE_IMAGE_FOLDER,
):
    # Create the output file
    with open(output_file_path, "w") as f:
        pass

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
        for row in transposed_matrix:
            # print(row)
            for index, content in enumerate(row):
                if index == 0:
                    strings.append(f"{content}")
                    if "\n" in content:
                        card_code = content.split("\n")[-1]
                        card_code_list.append(card_code)
                        # TODO: add card code for other type of cards
                elif index == 1:
                    strings.append(f"採用率:\t{content}")
                elif index == 2:
                    strings.append(f"平均採用張數:\t{content}")
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
        default="output.txt",
        help="Path to the output file",
    )
    parser.add_argument(
        "--download_images", "-d", action="store_true", help="Download images"
    )
    parser.add_argument(
        "--resize_images",
        "-r",
        action="store_true",
        help="Resize downloaded images",
    )

    args = parser.parse_args()

    format_for_blog(
        input_file_path=args.input_path,
        output_file_path=args.output_path,
        is_download_image=args.download_images,
        is_resize_image=args.resize_images,
    )


if __name__ == "__main__":
    main()
