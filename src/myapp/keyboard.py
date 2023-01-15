"""Representation of a keymap"""
import collections

from frozendict import frozendict

Keymap = collections.namedtuple(
    "Keymap",
    [
        "keys",
        "mapping",
        "char_mapping",
        "layers",
        "rolls",
        "free_keys",
        "hash",
        "definition",
        "name",
        "score",
    ],
)

Key = collections.namedtuple("Key", ["fingering", "score", "char", "locked"])
Keyboard = collections.namedtuple("Keyboard", ["keys", "rolls"])
Fingering = collections.namedtuple("Fingering", ["layer", "row", "hand", "column"])


class KeymapHelper:
    """Helper methods for Keymap"""

    _name = "Keymap"
    count = 0

    @classmethod
    def add_constraints_to_keymap(
        cls, constraints: dict, keymap: Keymap, chars: list[str]
    ) -> Keymap:
        for layer, rows in constraints.items():
            for row, hands in rows.items():
                for hand, columns in hands.items():
                    for column, char in columns.items():
                        key = cls.get_key(keymap, Fingering(layer, row, hand, column))
                        if key is not None:
                            keymap = cls.assign_char_to_key(
                                keymap, char, key, locked=True
                            )
                        keymap.free_keys.remove(keymap.mapping[key.fingering])
                        if char == "\\s":
                            char = " "
                        elif char == "\\n":
                            char = "\n"
                        try:
                            chars.remove(char)
                        except KeyError:
                            pass
        return keymap

    @classmethod
    def copy(cls, keymap, **override) -> Keymap:
        if not "name" in override.keys():
            cls.count += 1
            name = f"{cls._name}{cls.count}"
        else:
            name = override["name"]
        new_keymap = Keymap(
            override.get("keys", list(keymap.keys)),
            override.get("mapping", keymap.mapping),
            override.get("char_mapping", keymap.char_mapping),
            override.get("layers", keymap.layers),
            override.get("rolls", keymap.rolls),
            override.get("free_keys", keymap.free_keys),
            override.get("hash", list(keymap.hash)),
            override.get("definition", keymap.definition),
            name,
            override.get("score", keymap.score),
        )
        return new_keymap

    @classmethod
    def assign_char_to_key(
        cls, keymap: Keymap, char: str, key: Key, locked: bool = False
    ) -> Keymap:
        key = Key(key.fingering, key.score, char, locked)
        char_mapping = dict(keymap.char_mapping)
        char_mapping[char] = key.fingering
        new_keymap = cls.copy(
            keymap,
            char_mapping=frozendict(char_mapping),
            name=keymap.name,
            score=None,
        )
        new_keymap.keys[keymap.mapping[key.fingering]] = key
        new_keymap.hash[keymap.mapping[key.fingering]] = char
        return new_keymap

    @classmethod
    def set_score(cls, keymap: Keymap, score: int) -> Keymap:
        new_keymap = cls.copy(
            keymap,
            name=keymap.name,
            score=score,
        )
        return new_keymap

    @staticmethod
    def get_fingerings(keymap) -> list:
        for layer in keymap.definition["layers"]:
            for row in keymap.definition["rows"]:
                for hand in keymap.definition["hands"]:
                    for column in keymap.definition["columns"][hand]:
                        yield Fingering(layer, row, hand, column)

    @classmethod
    def get_hash(cls, keymap: Keymap) -> str:
        return "".join(keymap.hash)

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
    def get_rolls(cls, keymap: Keymap) -> dict[str]:
        rolls = {}
        for layer in keymap.definition["layers"]:
            for row in keymap.definition["rows"]:
                for hand in keymap.definition["hands"]:
                    prev = ""
                    for column in keymap.definition["columns"][hand]:
                        key = cls.get_key(keymap, Fingering(layer, row, hand, column))
                        if key is not None:
                            char = key.char
                        else:
                            char = ""
                        if prev and char:
                            rolls[char] = rolls.get(char, [])
                            rolls[char].append(prev)
                            rolls[prev] = rolls.get(prev, [])
                            rolls[prev].append(char)
                        prev = char
        return rolls

    @classmethod
    def new(cls, config: dict, name: str = None) -> Keymap:
        keyboard = KeyboardHelper.new(config)
        if not name:
            name = f"{cls._name}{cls.count}"

        rolls: dict(Fingering, dict[str, list[list[int]]]) = {}

        # Create layers
        keys: list(Key) = []
        mapping: dict[Fingering, int] = {}
        layers: dict(str, list[int]) = {}
        free_keys = []
        for layer in config["layout"]["definitions"]["layers"]:
            score_layer = config["score"]["layers"][layer]
            layers[layer] = []
            for fingering, key in keyboard.keys.items():
                fingering = Fingering(layer, *fingering[1:])
                key_score = key.score + score_layer
                mapping[fingering] = len(keys)
                layers[layer].append(len(keys))
                free_keys.append(len(keys))
                keys.append(Key(fingering, key_score, None, key.locked))
        free_keys = sorted(free_keys, key=lambda x: keys[x].score)

        # Compute rolls
        rolls = {}
        for ngram, length in {"bigram": 2}.items():
            rolls[ngram] = {}
            for key in keys:
                rolls[ngram][key.fingering] = cls.get_key_rolls(
                    key, keyboard, mapping, length
                )

        km_hash = ["X" for _ in keys]
        return Keymap(
            keys,
            frozendict(mapping),
            frozendict({}),
            frozendict(layers),
            frozendict(rolls),
            free_keys,
            km_hash,
            frozendict(config["layout"]["definitions"]),
            name,
            None,
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
                            if key.locked:
                                char = f"({char})"
                            else:
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
                    score = (
                        config["score"]["fingers"][hand][column]
                        + config["score"]["rows"][row]
                    )
                    # score = 1.01**score
                    keys[fingering] = Key(fingering, score, None, False)
                    rolls[row][hand].append(fingering)
        keyboard = Keyboard(frozendict(keys), frozendict(rolls))
        return keyboard
