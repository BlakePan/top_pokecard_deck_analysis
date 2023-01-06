SIMPLE_CASE = [
    "ルギアVSTAR",
    "ミュウVMAX",
    "ムゲンダイナVMAX",
    "キュレムVMAX",
    "オリジンパルキアVSTAR",
    "レジエレキVMAX",
    "オリジンディアルガVSTAR",
    "ヒスイ ダイケンキVSTAR",
    "ハピナスV",
    "こくばバドレックスVMAX",
    "ルナトーン",
    "プテラVSTAR",
    "ヒスイ ゾロアークVSTAR",
    "ガラル マタドガス",
    "ミュウツーV-UNION",
    "ロトムVSTAR",
    "クロススイッチャー",
    "かがやくムゲンダイナ",
]


def find_categories(pokemon_dict: dict, tool_dict: dict, energy_dict: dict) -> str:
    # identify this deck belongs to which categories (TODO: need more rules)

    # Initialize
    categories = []
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
    for card in SIMPLE_CASE:
        if card in poke_cards or card in tool_dict:
            categories.append(card)

    # "ゾロア"
    if "ゾロア" in poke_cards:
        if "ヒスイ ウインディ" in poke_cards:
            categories.append("ゾロア_ウインディ")
        else:
            categories.append("ゾロア")

    # "レジドラゴVSTAR"
    if "レジドラゴVSTAR" in poke_cards:
        if "アルセウスVSTAR" in poke_cards:
            categories.append("アル_レジドラゴVSTAR")
        else:
            categories.append("レジドラゴVSTAR")

    # "ギラティナVSTAR"
    if "ギラティナVSTAR" in poke_cards:
        if "キュワワー" in poke_cards:
            categories.append("LOST_ギラティナVSTAR")
        else:
            categories.append("Other_ギラティナVSTAR")

    # LOST
    if "キュワワー" in poke_cards:
        if "ヤミラミ" not in poke_cards:
            categories.append("Other_Lost")
        else:
            categories.append("LTB")

        if "空の封印石" in tool_cards:
            if "かがやくゲッコウガ" in poke_cards:
                categories.append(f"LTB_空の封印石_{basic_energies}")
            else:
                categories.append("LTB_空の封印石_other")
        if "フリーザー" in poke_cards and "ヤミラミ" not in poke_cards:
            categories.append("LTB_ウッウ")
        if "かがやくリザードン" in poke_cards:
            if "ヤミラミ" not in poke_cards:
                categories.append("LTB_リザードン")
            else:
                categories.append("LTB_ヤミラミ_リザードン")
        if "カイオーガ" in poke_cards:
            categories.append("LTB_カイオーガ")
        if "カイリューV" in poke_cards:
            categories.append("LTB_カイリュー")

    # "レジ"
    if (
        "レジギガス" in poke_cards
        and "レジドラゴ" in poke_cards
        and "レジスチル" in poke_cards
        and "レジロック" in poke_cards
        and "レジアイス" in poke_cards
        and "レジエレキ" in poke_cards
    ):
        categories.append("レジ")

    # "アルセウスVSTAR"
    if "アルセウスVSTAR" in poke_cards:
        if "メッソン" in poke_cards:
            categories.append("アルセウス裏工作")
        elif "ジュラルドンVMAX" in poke_cards:
            categories.append("アル_ジュラルドン")
        elif "そらをとぶピカチュウVMAX" in poke_cards:
            categories.append("アル_そらをとぶピカチュウ")

    if not categories:
        categories.append("others")

    return categories


if __name__ == "__main__":
    pass
