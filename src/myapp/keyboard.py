"""Representation of a keymap"""
import collections
import copy

Column = collections.namedtuple("Column", ["score"])
Hand = collections.namedtuple("Hand", ["columns"])
Row = collections.namedtuple("Row", ["hands", "score"])
Layer = collections.namedtuple("Layer", ["keyboard", "rows", "score", "name"])
Keymap = collections.namedtuple("Keymap", ["layers", "rolls", "definition", "name"])

Char = collections.namedtuple("Char", ["char", "score"])
Key = collections.namedtuple("Key", ["fingering", "score", "char"])
Keyboard = collections.namedtuple("Keyboard", ["rows", "rolls"])
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
        layer, row, hand, column = key.fingering
        key = Key(key.fingering, key.score * char.score, char.char)
        new_keymap = cls.copy(keymap)
        new_keymap.layers[layer].rows[row][hand][column] = key
        return new_keymap

    @classmethod
    def copy(cls, src: Keymap, name: str = None) -> Keymap:
        cls.count += 1
        if not name:
            name = f"{cls._name}{cls.count}"
        keymap = Keymap(copy.deepcopy(src.layers), src.rolls, src.definition, name)
        return keymap

    @classmethod
    def get_free_keys(cls, keymap: Keymap) -> list[Key]:
        # This can probably be optimized by storing the list at each level
        free_keys = []
        for layer in keymap.definition["layers"]:
            for row in keymap.definition["rows"]:
                for hand in keymap.definition["hands"]:
                    for column in keymap.definition["columns"][hand]:
                        key = cls.get_key(keymap, Fingering(layer, row, hand, column))
                        if key is not None and key.char is None:
                            free_keys.append(key)
        free_keys = sorted(free_keys, key=lambda x: x.score)
        return free_keys

    @staticmethod
    def get_key(keymap: Keymap, fingering: Fingering) -> Key:
        l, r, h, c = fingering
        try:
            return keymap.layers[l].rows[r][h][c]
        except KeyError:
            return None

    @classmethod
    def get_key_rolls(cls, keymap: Keymap, key: Key, length: int) -> list[list[Key]]:
        rolls = []
        roll_row = keymap.rolls[key.fingering.row][key.fingering.hand]
        key_index = roll_row.index(
            (key.fingering.row, key.fingering.hand, key.fingering.column)
        )
        start = max(0, key_index - length + 1)
        stop = min(len(roll_row) - length, key_index) + 1

        roll_fingering = [
            Fingering(key.fingering.layer, row, hand, column)
            for row, hand, column in roll_row
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

        layers = {}
        for layer in config["layout"]["definitions"]["layers"]:
            layers[layer] = LayerHelper.new(
                keyboard, config["score"]["layers"][layer], layer
            )

        return Keymap(layers, keyboard.rolls, config["layout"]["definitions"], name)

    @staticmethod
    def print(keymap, mode="char") -> None:
        lines = [f"# {keymap.name}"]
        middle = 0
        for layer in keymap.definition["layers"]:
            lines.append(f"## {keymap.layers[layer].name}")
            for row in keymap.definition["rows"]:
                hands = []
                for hand in keymap.definition["hands"]:
                    keys = []
                    for column in keymap.definition["columns"][hand]:
                        key = KeymapHelper.get_key(
                            keymap, Fingering(layer, row, hand, column)
                        )
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


class KeyboardHelper:
    """Helper methods for Keyboard"""

    @staticmethod
    def new(config: dict) -> Keyboard:
        rows: dict[str, Hand] = {}
        rolls: dict[str, list(str)] = {}
        for row, hands in config["layout"]["rows"].items():
            rows[row] = {}
            rolls[row] = {}
            for hand, columns in hands.items():
                roll = []
                rows[row][hand] = {}
                for column in columns:
                    fingering = (row, hand, column)
                    score = config["score"]["rows"][row]
                    score += config["score"]["fingers"][hand][column]
                    rows[row][hand][column] = Key(fingering, score, None)
                    roll.append(fingering)
                rolls[row][hand] = roll
        return Keyboard(rows, rolls)


class LayerHelper:
    """Helper methods for Layer"""

    @staticmethod
    def new(keyboard: Keyboard, score: float, name="Layer") -> Layer:
        new_rows = {}
        for row, hands in keyboard.rows.items():
            new_hands = {}
            for hand, columns in hands.items():
                new_columns = {}
                for column, key in columns.items():
                    fingering = Fingering(name, row, hand, column)
                    key_score = score + key.score
                    new_columns[column] = Key(fingering, key_score, None)
                new_hands[hand] = new_columns
            new_rows[row] = new_hands
        return Layer(keyboard, new_rows, score, name)
