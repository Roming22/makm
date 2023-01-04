"""Score a keymap"""
# import time
import typing

from keyboard import Key, Keymap, KeymapHelper


class Calculator:
    singleton = None

    def __init__(self):
        self.ngrams = {}
        self.ngrams_bonus = {}
        self.best_ngram_pair_score = {}
        self.worst_ngram_score = {}

    def set(self, corpus: dict, config: dict):
        ngrams = {
            "bigram": corpus["bigram_count"],
            "trigram": corpus["trigram_count"],
        }
        self.ngrams = {
            "bigram": {},
            "trigram": {},
        }
        self.ngrams_bonus = config["preferences"]["score"]["rolls"]
        self.best_ngram_pair_score = {}
        self.worst_ngram_score = {}
        for ng in ["bigram", "trigram"]:
            self.ngrams[ng] = {}
            self.best_ngram_pair_score[ng] = {}
            self.worst_ngram_score[ng] = {}
            bonus = self.ngrams_bonus[ng]
            for char in corpus["letter_count"]:
                self.ngrams[ng][char] = {}
                for ngram, count in ngrams[ng].items():
                    if char in ngram:
                        self.ngrams[ng][char][ngram] = count * bonus
                ngs = sorted(self.ngrams[ng][char].values())
                if len(ngs) > 1:
                    self.best_ngram_pair_score[ng][char] = ngs.pop() + ngs.pop()
                    self.worst_ngram_score[ng][char] = ngs[0]

    @classmethod
    def get(cls):
        if cls.singleton is None:
            cls.singleton = Calculator()
        return cls.singleton

    def get_score_for_key(
        self,
        key: Key,
        keymap: Keymap,
        missing_chars: list,
    ) -> typing.Tuple[float, float]:
        scale = 1000000
        base_score = self.get_base_score(keymap, key) / scale
        best_score = (
            self.get_best_score_lower_bound(keymap, missing_chars) / scale + base_score
        )
        worst_score = (
            self.get_worst_score_upper_bound(keymap, missing_chars) / scale + base_score
        )
        return best_score, worst_score

    def get_base_score(self, keymap: Keymap, key: Key) -> float:
        """Score with the populated keys"""
        score = key.score
        score += self.get_ngram_score_for_key(keymap, key, "bigram")
        score += self.get_ngram_score_for_key(keymap, key, "trigram")
        return score

    def get_ngram_score_for_key(self, keymap: Keymap, key: Key, ngram: str) -> float:
        ngrams = self.ngrams[ngram]
        rolls_fingering = KeymapHelper.get_key_rolls(
            keymap, key, len(next(iter(ngrams.keys())))
        )
        rolls = []
        for roll in rolls_fingering:
            ng = ""
            for fingering in roll:
                char = KeymapHelper.get_key(keymap, fingering).char
                if char:
                    ng += char
                else:
                    ng += " "
            rolls.append(ng)

        for ng, score in self.ngrams[ngram][key.char].items():
            if ng in rolls:
                return score
        return 0.0

    def get_best_score_lower_bound(self, keymap: Keymap, missing_chars: list) -> float:
        """This score must be equal or lower than the final score"""
        score = 0.0
        missing_chars = list(reversed(missing_chars))
        free_keys = KeymapHelper.get_free_keys(keymap)

        while missing_chars:
            char = missing_chars.pop()
            key = free_keys.pop()
            score += char.score * key.score
            score += self.worst_ngram_score["bigram"][char.char]
            # No trigrams
        return score

    def get_worst_score_upper_bound(self, keymap: Keymap, missing_chars: list) -> float:
        """This score must be equal or greater than the final score"""
        score = 0.0
        missing_chars = list(missing_chars)
        free_keys = KeymapHelper.get_free_keys(keymap)

        while missing_chars:
            # Key and chars are ordered by score/frequency
            # which ease calculating the max score for single keys
            # as easy as going through the sequence
            char = missing_chars.pop()
            key = free_keys.pop()
            score += char.score * key.score
            score += self.best_ngram_pair_score["bigram"][char.char]
            score += self.best_ngram_pair_score["trigram"][char.char]
        return score
