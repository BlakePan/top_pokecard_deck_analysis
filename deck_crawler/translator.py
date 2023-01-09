import json
from typing import Dict
from pathlib import Path

JP_CH_DICT_PATH = Path(__file__).parent / "assets/card_name_jp_ch_dictionary.json"
with open(JP_CH_DICT_PATH, "r") as f:
    JP_CH_DICT = json.load(f)

CODE_MAPPING_PATH = Path(__file__).parent / "assets/code_mapping.json"
with open(CODE_MAPPING_PATH, "r") as f:
    CODE_MAPPING = json.load(f)


def translate_jp_to_ch(card_name: str, jp_ch_dict: Dict = JP_CH_DICT):
    if card_name in jp_ch_dict:
        return jp_ch_dict[card_name]
    else:
        return card_name


def map_card_code(card_name:str, card_code: str):
    if card_name in CODE_MAPPING:
        for code_list in CODE_MAPPING[card_name]:
            if card_code in code_list:
                card_code = code_list[0]

    return card_code
