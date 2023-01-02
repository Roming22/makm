"""Score a keyboard layout"""
# import time
import typing

from keyboard import Key, Keyboard


class Calculator:
    singleton = None

    def __init__(self):
        self.ngrams = {}
        self.ngrams_bonus = {}
        self.best_ngram_pair_score = {}
        self.worst_ngram_score = {}

    def set(self, corpus: dict, config: dict):
        self.ngrams = {
            "bigram": corpus["bigram_count"],
            "trigram": corpus["trigram_count"],
        }
        self.ngrams_bonus = config["preferences"]["score"]["rolls"]
        self.best_ngram_pair_score = {}
        self.worst_ngram_score = {}
        for ng in ["bigram", "trigram"]:
            bonus = self.ngrams_bonus[ng]
            self.best_ngram_pair_score[ng] = {}
            self.worst_ngram_score[ng] = {}
            for char in corpus["letter_count"]:
                ngs = [
                    count * bonus
                    for _ng, count in self.ngrams[ng].items()
                    if char in _ng
                ]
                ngs = sorted(ngs)
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
        keyboard: Keyboard,
        missing_chars: list,
    ) -> typing.Tuple[float, float]:
        scale = 1000000
        base_score = self.get_base_score(key) / scale
        best_score = (
            self.get_best_score_lower_bound(keyboard, missing_chars) / scale
            + base_score
        )
        worst_score = (
            self.get_worst_score_upper_bound(keyboard, missing_chars) / scale
            + base_score
        )
        # print(best_score, worst_score)
        return best_score, worst_score

    def get_base_score(self, key: Key) -> float:
        """Score with the populated keys"""
        score = 0.0
        score += key.score * key.char.score
        ng_score = self.get_ngram_score_for_key(key, "bigram")
        ng_score = self.get_ngram_score_for_key(key, "trigram")
        score += ng_score
        return score

    def get_ngram_score_for_key(self, key: Key, ngram: str) -> float:
        ngrams = self.ngrams[ngram]
        roll_keys = key.get_rolls(len(next(iter(ngrams.keys()))))
        ngrams = {
            ng: count * self.ngrams_bonus[ngram]
            for ng, count in ngrams.items()
            if key.char.char in ng
        }
        for ng, score in ngrams.items():
            for roll in roll_keys:
                match = [[c, None] for c in ng]
                for i, k in enumerate(roll):
                    if k.char is not None and k.char.char == match[i][0]:
                        match[i][1] = True
                    else:
                        match[i][1] = False
                        break
                # Perfect match
                if not [f[1] for f in match if f[1] is not True]:
                    return score
                # Impossible roll
                if [f[1] for f in match if f[1] is False]:
                    break
        return 0.0

    def get_best_score_lower_bound(
        self, keyboard: Keyboard, missing_chars: list
    ) -> float:
        """This score must be equal or lower than the final score"""
        score = 0.0
        missing_chars = list(reversed(missing_chars))
        free_keys = keyboard.get_free_keys()

        while missing_chars:
            char = missing_chars.pop()
            key = free_keys.pop()
            score += char.score * key.score
            score += self.worst_ngram_score["bigram"][char.char]
            # No trigrams
        return score

    def get_worst_score_upper_bound(
        self, keyboard: Keyboard, missing_chars: list
    ) -> float:
        """This score must be equal or greater than the final score"""
        score = 0.0
        missing_chars = list(missing_chars)
        free_keys = keyboard.get_free_keys()

        while missing_chars:
            # Key and chars are ordered by score/frequency
            # which kaes calcuting the max score for single keys
            # as easy as going through the sequence
            char = missing_chars.pop()
            key = free_keys.pop()
            score += char.score * key.score
            score += self.best_ngram_pair_score["bigram"][char.char]
            score += self.best_ngram_pair_score["trigram"][char.char]
        return score
