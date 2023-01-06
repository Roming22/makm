"""Score a keymap"""
# import time
import typing

from keyboard import Key, Keymap, KeymapHelper


class Calculator:
    singleton = None

    def __init__(self):
        self.ngrams = {}
        self.ngrams_bonus = {}
        self.good_ngram_score = {}
        self.bad_ngram_score = {}

    def set(self, corpus: dict, config: dict) -> None:
        ngrams = {
            "bigram": corpus["bigram_count"],
            "trigram": corpus["trigram_count"],
        }
        self.ngrams = {
            "bigram": {},
            "trigram": {},
        }
        self.ngrams_bonus = config["preferences"]["score"]["rolls"]
        self.good_ngram_score = {}
        self.bad_ngram_score = {}
        for ng in ["bigram", "trigram"]:
            self.ngrams[ng] = {}
            self.good_ngram_score[ng] = {}
            self.bad_ngram_score[ng] = {}
            bonus = self.ngrams_bonus[ng]
            for char in corpus["letter_count"]:
                self.ngrams[ng][char] = {}
                for ngram, count in ngrams[ng].items():
                    if char in ngram:
                        self.ngrams[ng][char][ngram] = (1 + count) * bonus
                ngs = sorted(self.ngrams[ng][char].values())
                if len(ngs) > 1:
                    self.good_ngram_score[ng][char] = ngs[-1]
                    self.bad_ngram_score[ng][char] = ngs[0] + ngs[1]

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
        """Calculate the keymap score bounds

        Lower score must be equal or lower than the final score

        Upper score must be equal or greater than the final score

        I.e. there's a guarantee that the final score is between
        the upper and lower limits."""

        base_score = self.get_base_score(keymap, key)

        lower_score_limit = base_score
        upper_score_limit = base_score
        for char, best_key_index, worst_key_index in zip(
            missing_chars, keymap.free_keys, reversed(keymap.free_keys)
        ):
            best_key = keymap.keys[best_key_index]
            worst_key = keymap.keys[worst_key_index]
            lower_score_limit += char.score * best_key.score
            upper_score_limit += char.score * worst_key.score
            # lower_score_limit += self.bad_ngram_score["bigram"][char.char]
            # No trigrams for lower score.
            upper_score_limit += self.good_ngram_score["bigram"][char.char]
            upper_score_limit += self.good_ngram_score["trigram"][char.char]
            # print("lower", lower_score_limit, "upper", upper_score_limit)
        if lower_score_limit > upper_score_limit:
            raise Exception("Boom!")
        return (base_score, lower_score_limit, upper_score_limit)

    def get_base_score(self, keymap: Keymap, key: Key) -> float:
        """Score with the populated keys"""
        score = key.score
        score += self.get_ngram_score_for_key(keymap, key, "bigram")
        score += self.get_ngram_score_for_key(keymap, key, "trigram")
        # print("Base score:", score)
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
                    ng = None
                    break
            if ng:
                rolls.append(ng)

        for ng, score in self.ngrams[ngram][key.char].items():
            if ng in rolls:
                return score
        return 0.0
