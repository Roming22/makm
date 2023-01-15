"""Score a keymap"""
# import time
import typing

from myapp.keyboard import Fingering, Key, Keymap, KeymapHelper


class Calculator:
    singleton = None

    def __init__(self):
        self.corpus = {}
        self.fingers = {}
        self.score = {}

    def set(self, corpus: dict, config: dict) -> None:
        self.corpus = corpus["language"]
        self.score = config["keyboard"]["score"]
        self.score.update(config["preferences"]["score"])
        for hand in config["keyboard"]["layout"]["definitions"]["hands"]:
            self.fingers[hand] = self.fingers.get(hand, {})
            for column in config["keyboard"]["layout"]["definitions"]["columns"][hand]:
                self.fingers[hand][column] = [
                    r for r, v in config["keyboard"]["score"]["rows"].items() if v == 0
                ][0]

    @classmethod
    def get(cls):
        if cls.singleton is None:
            cls.singleton = Calculator()
        return cls.singleton

    def get_score(
        self,
        keymap: Keymap,
    ) -> float:
        """Calculate the keymap score"""

        score = 0.0
        fingers = dict(self.fingers)
        fingering_score_cache = {
            f: KeymapHelper.get_key(keymap, f).score for f in keymap.mapping.keys()
        }
        rolls = KeymapHelper.get_rolls(keymap)
        for corpus in self.corpus.values():
            language_score = 0.0
            for char, count in corpus["count"][1].items():
                # Base score based on char count
                fingering = keymap.char_mapping[self.translate_char(char)]
                base_score = fingering_score_cache[fingering] * count

                for tchar, count in corpus["count"][2][char].items():
                    tkey = keymap.char_mapping[self.translate_char(tchar)]

                    if tkey.layer == fingering.layer:
                        # Remove malus for bigrams on the same layer
                        base_score -= self.score["layers"][fingering.layer] * count

                    if tchar == char:
                        # Add repeat key bonus
                        base_score -= self.score["repeat"] * count
                    elif (
                        # Add same finger transition malus
                        tkey.hand == fingering.hand
                        and tkey.column == fingering.column
                    ):
                        base_score += self.score["same_finger"]

                # Add roll bonus
                try:
                    for tchar in rolls[char]:
                        base_score -= (
                            corpus["count"][2][char][tchar] * self.score["rolls"][2]
                        )
                except KeyError:
                    pass

                language_score += base_score
                fingers[fingering.hand][fingering.column] = fingering.row
            score += language_score * corpus["weight"] / corpus["size"]
        return score

    def translate_char(self, char: str) -> str:
        if char == " ":
            char = "\\s"
        elif char == "\n":
            char = "\\n"
        return char
