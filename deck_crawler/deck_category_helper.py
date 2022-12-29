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
]


def find_category(pokemon_dict: dict, tool_dict: dict, energy_dict: dict) -> str:
    # identify this deck belongs to which category (TODO: need more rules)
    category = "others"
    poke_cards = pokemon_dict.keys()
    tool_cards = tool_dict.keys()
    energy_cards = energy_dict.keys()

    basic_energies = []
    for e in energy_cards:
        if "基本" in e:
            basic_energies.append(e[2])
    basic_energies = "".join(sorted(basic_energies))

    for c in SIMPLE_CASE:
        if c in poke_cards:
            category = c
            break

    if category != "others":
        pass
    else:
        if "ゾロア" in poke_cards:
            if "ヒスイ ウインディ" in poke_cards:
                category = "ゾロア_ウインディ"
            else:
                category = "ゾロア"
        elif "レジドラゴVSTAR" in poke_cards:
            if "アルセウスVSTAR" in poke_cards:
                category = "アル_レジドラゴVSTAR"
            else:
                category = "レジドラゴVSTAR"
        elif "ギラティナVSTAR" in poke_cards:
            if "キュワワー" in poke_cards:
                category = "LOST_ギラティナVSTAR"
            else:
                category = "Other_ギラティナVSTAR"
        elif "キュワワー" in poke_cards:
            if "空の封印石" in tool_cards:
                if "かがやくゲッコウガ" in poke_cards:
                    category = f"LTB_空の封印石_{basic_energies}"
                else:
                    category = "LTB_空の封印石_other"
            elif "フリーザー" in poke_cards and "ヤミラミ" not in poke_cards:
                category = "LTB_ウッウ"
            elif "かがやくリザードン" in poke_cards:
                category = "LTB_リザードン" if "ヤミラミ" not in poke_cards else "LTB_ヤミラミ_リザードン"
            elif "ヤミラミ" not in poke_cards:
                category = "Other_Lost"
            elif "カイオーガ" in poke_cards:
                category = "LTB_カイオーガ"
            else:
                category = "LTB"
        elif (
            "レジギガス" in poke_cards
            and "レジドラゴ" in poke_cards
            and "レジスチル" in poke_cards
            and "レジロック" in poke_cards
            and "レジアイス" in poke_cards
            and "レジエレキ" in poke_cards
        ):
            category = "レジ"
        elif "アルセウスVSTAR" in poke_cards:
            if "メッソン" in poke_cards:
                category = "アルセウス裏工作"
            elif "ジュラルドンVMAX" in poke_cards:
                category = "アル_ジュラルドン"
            elif "そらをとぶピカチュウVMAX" in poke_cards:
                category = "アル_そらをとぶピカチュウ"

    return category


if __name__ == "__main__":
    pass
