"""Representation of a keyboard keys and layout"""
import collections
import copy


class Keyboard:
    """Representation of a keyboard, with its keys and layout"""

    _name = "Keyboard"
    count = 0

    def __init__(self, config: dict, name: str = None) -> None:
        self._config = config["layout"]["layers"]
        Keyboard.count += 1
        self.layer = {}
        if not name:
            name = f"{self._name}{self.count}"
        self.name = name

        layout = Layout(config)
        for layer in config["layout"]["layers"]:
            score = config["score"]["layers"][layer]
            self.layer[layer] = Layer(layout, score, layer)

        for layer, rows in config["constraints"].items():
            for row, hands in rows.items():
                for hand, fingers in hands.items():
                    print(layer, row, hand)
                    for finger, char in fingers.items():
                        print(char)
                        fingering = (row, hand, finger)
                        key = self.layer[layer].layout.row[row][fingering]
                        key.char = Char(char[0], char[1])
                        self.layer[layer].char[char] = key.char
                        self.layer[layer].free_keys.remove(key)
        self.print()

    def assign_char_to_key(self, char, key):
        key = self.layer[key.layer.name].layout.row[key.fingering[0]][key.fingering]
        key.char = char
        char.key = key
        layer = self.layer[key.layer.name]
        layer.char[char.char] = char
        layer.free_keys.remove(key)
        return key

    def copy(self, name: str = None):
        Keyboard._count += 1
        keyboard = copy.copy(self)
        if not name:
            name = f"{self._name}{self._count}"
        keyboard.name = name
        keyboard.layer = {}
        for lname, ldata in self.layer.items():
            keyboard.layer[lname] = ldata.copy()
        return keyboard

    def get_chars(self):
        chars = [self.layer[l].char for l in self._config]
        return collections.ChainMap(*chars)

    def get_free_keys(self):
        free_keys = []
        for layer in self._config:
            for key in self.layer[layer].free_keys:
                free_keys.append(key)
        free_keys = sorted(free_keys, key=lambda x: x.score)
        return free_keys

    def print(self, mode="char"):
        print(f"# {self.name}")
        for layer in self._config:
            self.layer[layer].print(mode)


class Layout:
    """Representation of a layer"""

    def __init__(self, config: dict) -> None:
        self._config = config["layout"]["rows"]
        self.row = {}
        for row, hands in config["layout"]["rows"].items():
            self.row[row] = {}
            for hand, fingers in hands.items():
                previous = False
                for finger in fingers:
                    fingering = (row, hand, finger)
                    score = config["score"]["rows"][row]
                    score += config["score"]["fingers"][hand][finger]
                    key = Key(fingering, score, previous)
                    self.row[row][fingering] = key
                    if previous:
                        previous.roll_next = key
                    previous = key
                previous.roll_next = False


class Layer:
    """Representation of a layer"""

    def __init__(self, layout: Layout, score: float, name="Layer") -> None:
        self.char = {}
        self.free_keys = []
        self.layout = copy.deepcopy(layout)
        self.name = name
        self.score = score
        for row, hands in self.layout._config.items():
            for hand, fingers in hands.items():
                for finger in fingers:
                    key = self.layout.row[row][(row, hand, finger)]
                    key.layer = self
                    key.score += score
                    self.free_keys.append(key)

    def copy(self):
        layer = copy.copy(self)
        layer.layout = copy.deepcopy(self.layout)
        layer.free_keys = []
        for row, hands in layer.layout._config.items():
            for hand, fingers in hands.items():
                previous = False
                for finger in fingers:
                    fingering = (row, hand, finger)
                    key = layer.layout.row.get(row, {}).get(fingering)
                    if previous is not False:
                        previous.roll_next = key
                    if key.char is None:
                        layer.free_keys.append(key)
                    previous = key
                key.roll_next = False
                previous.roll_next = key
        return layer

    def print(self, mode):
        print(f"## {self.name}")
        lines = []
        middle = 0
        for row, hands in self.layout._config.items():
            line = ""
            for hand, fingers in hands.items():
                for finger in fingers:
                    fingering = (row, hand, finger)
                    key = self.layout.row.get(row, {}).get(fingering)
                    char = " "
                    if mode == "char":
                        if key and key.char:
                            char = key.char.char
                    elif mode == "heat":
                        if key:
                            char = key.score
                    line += f"[{char}]"
                line += " | "
            lines.append(line)
            middle = max(middle, line.index("|"))
        for line in lines:
            line = " " * (middle - line.index("|")) + line[:-3]
            print(line)


class Key:
    """Representation of a key"""

    def __init__(self, fingering: tuple, score: float, roll_previous=None):
        self.char = None
        self.fingering = fingering
        self.layer = None
        self.score = score

        # Help figuring out ngrams
        self.roll_previous = roll_previous
        self.roll_next = None

    def get_rolls(self, count) -> list:
        key = self
        previous_roll = [key]
        while len(previous_roll) < count:
            if key.roll_previous:
                key = key.roll_previous
                previous_roll.append(key)
            else:
                previous_roll.clear()
                break
        if previous_roll and len(previous_roll) != count:
            raise Exception(
                f"Bad previous_roll has been generated, got {len(previous_roll)} instead of {count}"
            )
        key = self
        next_roll = [key]
        while len(next_roll) < count:
            if key.roll_next:
                key = key.roll_next
                next_roll.append(key)
            else:
                next_roll.clear()
                break
        if next_roll and len(next_roll) != count:
            raise Exception(
                f"Bad next_roll has been generated, got {len(next_roll)} instead of {count}"
            )
        rolls = [r for r in [previous_roll, next_roll] if r]
        return rolls


class Char:
    """Representation of a character"""

    def __init__(self, char, score):
        self.char = char
        self.key = None
        self.score = score
