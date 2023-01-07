"""Representation of a keymap"""
import collections

from frozendict import frozendict

Layer = collections.namedtuple("Layer", ["keyboard", "rows", "score", "name"])
Keymap = collections.namedtuple(
    "Keymap", ["keys", "mapping", "rolls", "free_keys", "definition", "name"]
)

Char = collections.namedtuple("Char", ["char", "score"])
Key = collections.namedtuple("Key", ["fingering", "score", "char"])
Keyboard = collections.namedtuple("Keyboard", ["keys", "rolls"])
Fingering = collections.namedtuple("Fingering", ["layer", "row", "hand", "column"])


class KeymapHelper:
    """Helper methods for Keymap"""

    _name = "Keymap"
    count = 0

    @classmethod
    def add_constraints_to_keymap(cls, constraints, corpus, keymap: Keymap) -> Keymap:
        corpus_dict = {c.char: c for c in corpus}
        removed_chars = set()
        for layer, rows in constraints.items():
            for row, hands in rows.items():
                for hand, columns in hands.items():
                    for column, c in columns.items():
                        char = corpus_dict.get(c, Char(c, 0))
                        key = cls.get_key(keymap, Fingering(layer, row, hand, column))
                        if key is not None:
                            if char in corpus:
                                removed_chars.add(char)
                            keymap = cls.assign_char_to_key(keymap, char, key)
        for char in removed_chars:
            corpus.remove(char)
        return keymap

    @classmethod
    def assign_char_to_key(cls, keymap: Keymap, char: Char, key: Key) -> Keymap:
        key = Key(key.fingering, key.score * char.score, char.char)
        cls.count += 1
        name = f"{cls._name}{cls.count}"
        index = keymap.mapping[key.fingering]
        split_at = keymap.free_keys.index(index)
        free_keys = list(keymap.free_keys[0:split_at])
        free_keys.extend(keymap.free_keys[split_at + 1 :])
        if index in free_keys:
            raise Exception("Bad key removed")
        new_keymap = Keymap(
            list(keymap.keys),
            keymap.mapping,
            keymap.rolls,
            free_keys,
            keymap.definition,
            name,
        )
        new_keymap.keys[keymap.mapping[key.fingering]] = key
        return new_keymap

    @staticmethod
    def get_fingerings(keymap) -> list:
        for layer in keymap.definition["layers"]:
            for row in keymap.definition["rows"]:
                for hand in keymap.definition["hands"]:
                    for column in keymap.definition["columns"][hand]:
                        yield Fingering(layer, row, hand, column)

    @staticmethod
    def get_key(keymap: Keymap, fingering: Fingering) -> Key:
        try:
            return keymap.keys[keymap.mapping[fingering]]
        except KeyError:
            return None

    @staticmethod
    def get_key_rolls(
        key: Key, keyboard: Keyboard, mapping: dict[Fingering, int], length: int
    ) -> list[list[int]]:
        layer, row, hand, column = key.fingering
        rolls = []
        roll_row = keyboard.rolls[row][hand]
        key_index = roll_row.index((None, row, hand, column))
        start = max(0, key_index - length + 1)
        stop = min(len(roll_row) - length, key_index) + 1

        roll_fingering = [
            mapping[Fingering(layer, row, hand, column)]
            for _, row, hand, column in roll_row
        ]

        for i in range(start, stop):
            rolls.append(roll_fingering[i : i + length])
        return rolls

    @classmethod
    def new(cls, config: dict, name: str = None) -> Keymap:
        keyboard = KeyboardHelper.new(config)
        cls.count += 1
        if not name:
            name = f"{cls._name}{cls.count}"

        rolls: dict(Fingering, dict[str, list[list[int]]]) = {}

        # Create layers
        keys: list(Key) = []
        mapping: dict[Fingering, int] = {}
        free_keys = []
        for layer in config["layout"]["definitions"]["layers"]:
            for fingering, key in keyboard.keys.items():
                fingering = Fingering(layer, *fingering[1:])
                key_score = config["score"]["layers"][layer] + key.score
                key_score = 0.99 ** (2 * key_score)
                mapping[fingering] = len(keys)
                free_keys.append(len(keys))
                keys.append(Key(fingering, key_score, None))
        free_keys = sorted(free_keys, key=lambda x: keys[x].score, reverse=True)

        # Compute rolls
        rolls = {}
        for ngram, length in {"bigram": 2, "trigram": 3}.items():
            rolls[ngram] = {}
            for key in keys:
                rolls[ngram][key.fingering] = cls.get_key_rolls(
                    key, keyboard, mapping, length
                )

        return Keymap(
            keys,
            frozendict(mapping),
            frozendict(rolls),
            free_keys,
            frozendict(config["layout"]["definitions"]),
            name,
        )

    @classmethod
    def print(cls, keymap, mode="char") -> None:
        lines = [f"# {keymap.name}"]
        middle = 0
        for layer in keymap.definition["layers"]:
            lines.append(f"## {layer}")
            for row in keymap.definition["rows"]:
                hands = []
                for hand in keymap.definition["hands"]:
                    keys = []
                    for column in keymap.definition["columns"][hand]:
                        key = cls.get_key(keymap, Fingering(layer, row, hand, column))
                        if key:
                            char = " "
                            if mode == "char":
                                char = key.char if key.char else char
                            elif mode == "score":
                                char = key.score
                            char = f"[{char}]"
                            keys.append(char)
                    hands.append("".join(keys))
                line = " | ".join(hands)
                lines.append(line)
                middle = max(middle, line.index("|"))
        for line in lines:
            if "|" in line:
                line = " " * (middle - line.index("|")) + line
            print(line)
        print(flush=True)

    @classmethod
    def save(cls, keymap) -> None:
        with open(f"{keymap.name}.csv", "w") as f:
            for layer in keymap.definition["layers"]:
                for row in keymap.definition["rows"]:
                    keys = []
                    for hand in keymap.definition["hands"]:
                        for column in keymap.definition["columns"][hand]:
                            key = cls.get_key(
                                keymap, Fingering(layer, row, hand, column)
                            )
                            char = ""
                            if key and key.char:
                                char = key.char
                            keys.append(char)
                    print(keys)
                    f.write("\t".join(keys))
                    f.write("\n")


class KeyboardHelper:
    """Helper methods for Keyboard"""

    @staticmethod
    def new(config: dict) -> Keyboard:
        keys: dict = {}
        rolls: dict = {}
        for row, hands in config["layout"]["rows"].items():
            rolls[row] = {}
            for hand, columns in hands.items():
                rolls[row][hand] = []
                for column in columns:
                    fingering = Fingering(None, row, hand, column)
                    score = config["score"]["rows"][row]
                    score += config["score"]["fingers"][hand][column]
                    keys[fingering] = Key(fingering, score, None)
                    rolls[row][hand].append(fingering)
        keyboard = Keyboard(frozendict(keys), frozendict(rolls))
        return keyboard
