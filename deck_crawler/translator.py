import copy
import json
from pathlib import Path
from typing import Dict

CODE_MAPPING_PATH = Path(__file__).parent / "assets/card_mapping.json"
with open(CODE_MAPPING_PATH, "r") as f:
    CODE_MAPPING = json.load(f)


def translate_jp_to_ch(card_name: str, jp_ch_dict: Dict = CODE_MAPPING) -> str:
    """Translate card name from Japanese to Chinese
    by using a self-built dictionary

    Args:
        card_name (str): Japanese card name
        jp_ch_dict (Dict, optional): Self-built dictionary.
        Defaults to CODE_MAPPING.

    Returns:
        str: Translated card name
    """
    if card_name in jp_ch_dict:
        return jp_ch_dict[card_name]["ch_name"]
    else:
        return card_name


def map_card_code(
    card_name: str, card_code: str, mapping_dict: Dict = CODE_MAPPING
) -> str:
    """Some cards with the same effect have different card codes,
    because the rarity is different. This function can map codes
    from cards with the same effect to the one for repesentation.

    Args:
        card_name (str): Japanese card name
        card_code (str): Input card code
        mapping_dict (Dict, optional): Self-built dictionary.
        Defaults to CODE_MAPPING.

    Returns:
        str: Mapped card code
    """
    if card_name in mapping_dict:
        for code_list in mapping_dict[card_name]["code_list"]:
            if card_code in code_list:
                card_code = code_list[0]
                break

    return card_code


def translate_deck(deck: Dict) -> Dict:
    """Translate card names in a deck object from Japanese to Chinese

    Args:
        deck (Dict): A deck object whose card names are Japanese

    Returns:
        Dict: A deck object whose card names are Chinese
    """

    translated_deck = copy.deepcopy(deck)

    for translate_field in [
        "pokemons",
        "tools",
        "supporters",
        "stadiums",
        "energies",
    ]:
        cards = deck[translate_field]
        temp_dict = copy.deepcopy(cards)

        for card in cards.keys():
            # Extract card name and card code
            if "\n" in card:
                card_name, card_code = card.split("\n")
                card_code = map_card_code(card_name, card_code)
            else:
                card_name, card_code = card, None

            # Translate
            card_name = translate_jp_to_ch(card_name)

            # Form new card name
            if card_code:
                card_name_new = card_name + "\n" + card_code
            else:
                card_name_new = card_name

            # Update the deck object
            if card_name_new != card:
                if card_name_new not in temp_dict:
                    temp_dict[card_name_new] = 0
                temp_dict[card_name_new] += temp_dict[card]
                temp_dict.pop(card)

        translated_deck[translate_field] = temp_dict

    return translated_deck
