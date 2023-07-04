import json
import os
import re
from typing import List

item_metadata = []
with open("./items.json", "r") as item_json:
    item_metadata = json.load(item_json)


class GloomhavenCard:
    random_item_deck_re = re.compile(r"gh-\d\d\da")
    item_qualifier_re = re.compile(r"gh-(\d\d\d[ab]?)")
    item_number_re = re.compile(r"gh-(\d\d\d)")

    @property
    def item_number(self) -> int:
        search = self.item_number_re.search(self.front_path)
        return int(search.group(1))

    def __init__(self, front_path: str):
        self.front_path = front_path
        self.back_path = front_path[:-4] + "-back.png"
        self.is_random_item_deck = re.search(self.random_item_deck_re, front_path) is not None
        self.item_json = self._find_item_entry()
        self.item_count = self.item_json.get("count", 1) or 1

    def _find_item_entry(self) -> dict:
        for item_md in item_metadata:
            if item_md["number"] == self.item_number:
                return item_md
        return {}

    def front_render(self) -> str:
        return "\\includegraphics[width=44mm,height=68mm]{" + self.front_path + "}"
    
    def back_render(self) -> str:
        return "\\includegraphics[width=44mm,height=68mm]{" + self.back_path + "}"
    
    @classmethod
    def copy(cls, card: "GloomhavenCard") -> "GloomhavenCard":
        return cls(card.front_path)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, GloomhavenCard) and self.front_path == __o.front_path

    def __lt__(self, __o: object) -> bool:
        if not isinstance(__o, GloomhavenCard):
            raise ValueError("Cannot compare different types")
        
        m_path_qual = self.item_qualifier_re.search(self.front_path).group(1)
        t_path_qual = self.item_qualifier_re.search(__o.front_path).group(1)
        return m_path_qual < t_path_qual

    def __hash__(self) -> int:
        return hash(self.front_path)
    

def generate_cards() -> List[List[GloomhavenCard]]:
    cards = []

    for (dirpath, _, filenames) in os.walk("."):
      for filename in filenames:
        if filename.endswith('.png') and not "back" in filename: 
            cards.append(GloomhavenCard(os.sep.join([dirpath, filename])))

    cards = sorted(cards)

    expanded_cards = []
    for card in cards:
        if not card.is_random_item_deck:
            for _ in range(0, card.item_count):
                expanded_cards.append(GloomhavenCard.copy(card))
        else:
            expanded_cards.append(GloomhavenCard.copy(card))

    gridded_cards = []
    row = []
    card_count = 0

    while card_count < len(expanded_cards):
        if card_count % 4 == 0 and len(row) > 0:
            gridded_cards.append(row)
            row = []
        row.append(GloomhavenCard.copy(expanded_cards[card_count]))
        card_count += 1

    return gridded_cards


def render() -> str:
    cards_matrix = generate_cards()

    # render the fronts
    table_contents = ""
    for row in cards_matrix:
        table_contents += " &\n".join([c.front_render() for c in row])
        table_contents = table_contents.strip()
        table_contents += "\\\\ \n"

    front_table = (
        "{\\setlength{\\tabcolsep}{1mm}\n"
        "\\begin{longtable}{llll}\n"
        f"{table_contents}"
        "\\end{longtable}}\n"
    )

    # render the backs
    table_contents = ""
    for row in cards_matrix:
        table_contents += " &\n".join([c.back_render() for c in row[::-1]])
        table_contents = table_contents.strip()
        table_contents += "\\\\ \n"

    back_table = (
        "{\\setlength{\\tabcolsep}{1mm}\n"
        "\\begin{longtable}{llll}\n"
        f"{table_contents}"
        "\\end{longtable}}\n"
    )

    return (
        "\\let\\mypdfximage\\pdfximage\n"
        "\\def\\pdfximage{\\immediate\\mypdfximage}\n"
        "\\documentclass{minimal}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage[a4paper,margin=1mm]{geometry}\n"
        "\\usepackage{longtable}\n"
        "\\begin{document}\n"
        "\\noindent\n"
        f"{front_table}"
        "\\newpage\n"
        f"{back_table}"
        "\\end{document}\n"
    )


if __name__ == "__main__":
    with open("main.tex", "w") as f:
        f.write(render())

    os.system("pdflatex main.tex")
