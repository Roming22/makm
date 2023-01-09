"""Score a keymap"""
# import time
import typing

from myapp.keyboard import Fingering, Key, Keymap, KeymapHelper


class Calculator:
    singleton = None

    def __init__(self):
        self.corpus = {}
        self.score = {}

    def set(self, corpus: dict, config: dict) -> None:
        self.score = config["keyboard"]["score"]
        self.corpus = corpus

        self.outgoing_bigrams = {
            char: sorted(self.corpus["bigram"][char].values(), reverse=True)
            for char in corpus["char"].keys()
        }
        self.incoming_bigrams = {
            char: sorted(
                [
                    self.corpus["bigram"][c].get(char, 0)
                    for c in self.corpus["char"].keys()
                ],
                reverse=True,
            )
            for char in corpus["char"].keys()
        }

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
        lower_score_limit, upper_score_limit = self.get_limits(keymap, missing_chars)

        return (
            base_score,
            base_score + lower_score_limit,
            base_score + upper_score_limit,
        )

    def get_base_score(self, keymap: Keymap, key: Key) -> float:
        """Score with the populated keys"""
        layer_score = self.score["layers"][key.fingering.layer]
        # Key score includes all incoming/outgoing bigrams, key position and layer penalty.
        score = key.score

        # Remove the layer penalty on bigrams that share the same layer
        for index in keymap.layers[key.fingering.layer]:
            try:
                char = keymap.keys[index].char
            except KeyError:
                char = None
            if char:
                try:
                    score -= self.corpus["bigram"][char][key.char] * (layer_score - 1)
                    score -= self.corpus["bigram"][key.char][char] * (layer_score - 1)
                except KeyError:
                    pass

        # Penalty on same column bigram
        column_score = self.score["same"]["column"]
        for row in keymap.definition["rows"]:
            key2 = KeymapHelper.get_key(
                keymap,
                Fingering(
                    key.fingering.layer, row, key.fingering.hand, key.fingering.column
                ),
            )
            if key2:
                char = key2.char
                try:
                    score += self.corpus["bigram"][char][key.char] * column_score
                    score += self.corpus["bigram"][key.char][char] * column_score
                except:
                    pass

        # Grant a bonus for rolls
        score += self.get_roll_score_for_key(keymap, key)
        return score

    def get_roll_score_for_key(self, keymap: Keymap, key: Key) -> float:
        rolls_fingering = keymap.rolls["bigram"][key.fingering]
        score = 0.0
        layer_score = self.score["layers"][key.fingering.layer]
        for roll in rolls_fingering:
            chars: list[str] = []
            for key_index in roll:
                char = keymap.keys[key_index].char
                if char is None:
                    chars.clear()
                    break
                chars.append(char)
            if chars:
                # The layer is not taken into account, as the penalty
                # has already been removed in a prior step.
                try:
                    score -= self.corpus["bigram"][chars[0]][chars[1]] * (
                        1 - self.score["rolls"]["bigram"]
                    )
                except:
                    pass
                try:
                    score -= self.corpus["bigram"][chars[1]][chars[0]] * (
                        1 - self.score["rolls"]["bigram"]
                    )
                except:
                    pass
        return score

    def get_limits(self, keymap, missing_chars):
        lower_score_limit = 0.0
        upper_score_limit = 0.0
        roll_score = self.score["rolls"]["bigram"]
        column_score = self.score["same"]["column"]
        for char, best_key_index, worst_key_index in zip(
            missing_chars, keymap.free_keys, reversed(keymap.free_keys)
        ):

            # Assign the best key to the best char
            key = keymap.keys[best_key_index]
            score = char.score * key.score
            layer_score = self.score["layers"][key.fingering.layer]
            # Apply same layer bonus to the best bigrams
            for i in range(
                0,
                len(keymap.definition["rows"])
                * len(keymap.definition["hands"])
                * len(keymap.definition["columns"])
                - 1,
            ):
                try:
                    score -= self.outgoing_bigrams[char.char][i] * (layer_score - 1)
                    score -= self.incoming_bigrams[char.char][i] * (layer_score - 1)
                except IndexError:
                    pass
            # Apply roll bonuses to the best bigrams
            for i in range(0, 2):
                score -= (
                    self.outgoing_bigrams[char.char][i] * layer_score * (1 - roll_score)
                )
                score -= (
                    self.incoming_bigrams[char.char][i] * layer_score * (1 - roll_score)
                )
            lower_score_limit += score

            # Assign the worst key to the best char
            key = keymap.keys[worst_key_index]
            score = char.score * key.score
            layer_score = self.score["layers"][key.fingering.layer]
            # Apply a single roll bonus to the worst bigram
            score -= (
                self.outgoing_bigrams[char.char][-1] * layer_score * (1 - roll_score)
            )
            score -= (
                self.incoming_bigrams[char.char][-1] * layer_score * (1 - roll_score)
            )
            # Apply same column malus to best bigrams
            for i in range(0, len(keymap.definition["rows"]) - 1):
                score += self.outgoing_bigrams[char.char][i] * column_score
                score += self.incoming_bigrams[char.char][i] * column_score
            # No layer bonus
            upper_score_limit += score

        if lower_score_limit > upper_score_limit:
            raise Exception("Boom!")

        return lower_score_limit, upper_score_limit
