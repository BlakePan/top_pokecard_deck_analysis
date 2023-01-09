import argparse
import numpy as np
import pandas as pd
from deck_crawler.translator import translate_jp_to_ch


# Parse the command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", required=True, help="Path to the input Excel file")
parser.add_argument(
    "--output", "-o", default="output.txt", help="Path to the output file"
)
args = parser.parse_args()

# Set the range of the matrix
start_row = 0
end_row = 2
start_col = 5
sheet_names = [
    ("pokemons", "寶可夢"),
    ("tools", "物品"),
    ("supporters", "支援者"),
    ("stadiums", "競技場"),
    ("energies", "能量"),
]

# Create file
with open(args.output, "w") as f:
    pass

# Loop through each sheet in the file
for sheet_index, sheet_name in enumerate(sheet_names):
    sheet_name_eng, sheet_name_ch = sheet_name

    # Read the sheet data from the Excel file
    df_sheet = pd.read_excel(args.input, sheet_name=sheet_name_eng)

    # Determine the dimensions of the matrix
    _, num_cols = df_sheet.shape
    end_col = num_cols

    # Extract the matrix of values from the DataFrame within a specified range
    column_names = df_sheet.columns.to_numpy()[start_col:]
    data = df_sheet.iloc[start_row:end_row, start_col:end_col].values
    matrix = np.vstack([column_names, data])

    # Transpose the matrix using the T attribute of the numpy library
    transposed_matrix = matrix.T

    # Convert the transposed matrix to a list of strings with newlines
    strings = []
    for row in transposed_matrix:
        # print(row)
        for index, content in enumerate(row):
            if index == 0:
                if "\n" in content:
                    card_name, card_code = content.split("\n")
                    card_name = translate_jp_to_ch(card_name)
                    content = f"{card_name}\n{card_code}"
                else:
                    content = translate_jp_to_ch(content)
                strings.append(f"{content}")
            elif index == 1:
                strings.append(f"採用率:\t{content}")
            elif index == 2:
                strings.append(f"平均採用張數:\t{content}")
        strings.append("")

    # Output the strings to a file
    with open(args.output, "a") as f:
        f.write(sheet_name_ch + "\n\n")
        for s in strings:
            f.write(s + "\n")
