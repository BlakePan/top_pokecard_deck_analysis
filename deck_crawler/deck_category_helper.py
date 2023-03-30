import copy
from .utils.translator import translate_jp_to_ch


SIMPLE_CASE = [
    ("ルギアVSTAR", 2),  # (key card name, required number)
    ("ミュウVMAX", 2),
    ("ムゲンダイナVMAX", 2),
    ("キュレムVMAX", 2),
    ("オリジンパルキアVSTAR", 2),
    ("レジエレキVMAX", 2),
    ("オリジンディアルガVSTAR", 2),
    ("ヒスイ ダイケンキVSTAR", 2),
    ("ハピナスV", 2),
    ("こくばバドレックスVMAX", 2),
    ("ルナトーン", 4),
    ("プテラVSTAR", 1),
    ("ヒスイ ゾロアークVSTAR", 3),
    ("ミュウツーV-UNION", 1),
    ("ロトムVSTAR", 2),
    ("クロススイッチャー", 2),
    ("かがやくムゲンダイナ", 1),
    ("カラマネロVMAX", 1),
    ("ダークライVSTAR", 2),
    ("そらをとぶピカチュウVMAX", 1),
    ("アローラロコンVSTAR", 2),
    ("ミライドンex", 2),
    ("サーナイトex", 1),
    ("パフュートンex", 2),
    ("レックウザVMAX", 2),
    ("アルセウスVSTAR", 2),
    ("れんげきウーラオスVMAX", 2),
    ("はくばバドレックスVMAX", 2),
    ("レジドラゴVSTAR", 2),
    ("バシャーモVMAX", 2),
    ("ヨクバリスVMAX", 2),
]


def find_categories(
    pokemon_dict: dict, tool_dict: dict, energy_dict: dict
) -> str:
    # identify this deck belongs to which categories (TODO: need more rules)

    # Initialize
    categories = []
    pokemon_dict_strip_name = {}
    for card_name, num_cards in pokemon_dict.items():
        strip_card_name = card_name.split("\n")[0]
        if strip_card_name not in pokemon_dict_strip_name:
            pokemon_dict_strip_name[strip_card_name] = 0
        pokemon_dict_strip_name[strip_card_name] += num_cards
    poke_cards = [card.split("\n")[0] for card in pokemon_dict.keys()]
    tool_cards = tool_dict.keys()
    energy_cards = energy_dict.keys()

    # Collect basic energies
    basic_energies = []
    for e in energy_cards:
        if "基本" in e:
            basic_energies.append(e[2])
    basic_energies = "".join(sorted(basic_energies))

    # For the simple case that once a card appeard in the deck
    # then the deck belongs to a category
    for card_name, required_num in SIMPLE_CASE:
        card_dict_list = [pokemon_dict_strip_name, tool_dict]
        for card_dict in card_dict_list:
            if card_name in card_dict and card_dict[card_name] >= required_num:
                categories.append(card_name)

    # "ゾロア"
    if "ゾロア" in poke_cards:
        if "ヒスイ ウインディ" in poke_cards:
            categories.append("索羅風速狗")
        else:
            categories.append("幻影索羅亞克")

    # "ギラティナVSTAR"
    if "ギラティナVSTAR" in poke_cards:
        if "キュワワー" in poke_cards or "ジュペッタ" in poke_cards:
            categories.append("放逐_騎拉帝納VSTAR")
        else:
            categories.append("Other_騎拉帝納VSTAR")

    # LOST
    if "キュワワー" in poke_cards and "ギラティナVSTAR" not in poke_cards:
        if "ヤミラミ" not in poke_cards:
            categories.append("Other_Lost")
        else:
            categories.append("LTB")

        if "空の封印石" in tool_cards:
            if "かがやくゲッコウガ" in poke_cards:
                categories.append(f"LTB_空之封印石_{basic_energies}")
            else:
                categories.append("LTB_空之封印石_other")

        if "フリーザー" in poke_cards and "ヤミラミ" not in poke_cards:
            categories.append("LTB_古月鳥")

        if "かがやくリザードン" in poke_cards:
            if "ヤミラミ" not in poke_cards:
                categories.append("LTB_噴火龍")
            else:
                categories.append("LTB_勾魂眼_噴火龍")

        if "カイオーガ" in poke_cards:
            categories.append("LTB_蓋歐卡")

        if "カイリューV" in poke_cards:
            categories.append("LTB_快龍V")

        if "ヒスイ ヌメルゴンVSTAR" in poke_cards:
            categories.append("LTB_洗翠黏美龍VSTAR")

    # "レジ"
    if (
        "レジギガス" in poke_cards
        and "レジドラゴ" in poke_cards
        and "レジスチル" in poke_cards
        and "レジロック" in poke_cards
        and "レジアイス" in poke_cards
        and "レジエレキ" in poke_cards
    ):
        categories.append("柱神")

    # "アルセウスVSTAR"
    if "アルセウスVSTAR" in poke_cards:
        # if "メッソン" in poke_cards:
        #     categories.append("アルセウス裏工作")
        if "ジュラルドンVMAX" in poke_cards:
            categories.append("阿爾_鋁鋼龍VMAX")
        elif "そらをとぶピカチュウVMAX" in poke_cards:
            categories.append("阿爾_飛天皮VMAX")
        elif "はくばバドレックスVMAX" in poke_cards:
            categories.append("阿爾_白馬VMAX")
        elif "レジドラゴVSTAR" in poke_cards:
            categories.append("阿爾_雷吉鐸拉戈VSTAR")
        elif "ギラティナVSTAR" in poke_cards:
            categories.append("阿爾_騎拉帝納VSTAR")

        is_other_V = False
        for pokemon in poke_cards:
            if (
                "アルセウスV" not in pokemon
                and "V" in pokemon
                and pokemon != "ドラピオンV"
                and pokemon != "ネオラントV"
            ):
                is_other_V = True
                break
        if not is_other_V:
            categories.append("純阿爾VSTAR")

    # "ルギアVSTAR"
    if "ルギアVSTAR" in poke_cards:
        if "バンギラスV" in poke_cards or "イシヘンジン" in poke_cards:
            categories.append("一擊_洛奇亞")

    # "ルギアVSTAR"
    if "サーナイトex" in poke_cards:
        if "ザシアンV" in poke_cards:
            categories.append("沙奈朵_蒼響")
        if "ミュウツーV-UNION" in poke_cards:
            categories.append("沙奈朵_超夢V-UNION")

    if "ミライドンex" in poke_cards and pokemon_dict_strip_name["ミライドンex"] >= 2:
        if "レジエレキVMAX" in poke_cards and pokemon_dict_strip_name["レジエレキVMAX"] >= 2:
            if "モココ" not in poke_cards:
                categories.append("密勒頓ex_電柱")
            else:
                categories.append("密勒頓ex_電柱_茸茸羊")
        elif "モココ" in poke_cards:
            categories.append("密勒頓ex_茸茸羊")
        else:
            categories.append("密勒頓ex_other")

    if not categories:
        categories.append("others")

    categories = [translate_jp_to_ch(c) for c in categories]
    return categories


if __name__ == "__main__":
    pass
