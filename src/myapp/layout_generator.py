"""Generate keymap layouts"""
import random
import time

from myapp.keyboard import Fingering, Keymap, KeymapHelper
from myapp.layout_calculator import Calculator


def generate(corpus: dict, config: dict):
    Calculator.get().set(corpus, config)

    # Create template keymap
    keymap = KeymapHelper.new(config["keyboard"])
    keymap = KeymapHelper.add_constraints_to_keymap(
        config["keyboard"]["constraints"], keymap, corpus["char"]
    )
    KeymapHelper.print(keymap)
    print()

    # Create initial population
    keymaps: list[Keymap] = []
    while len(keymaps) < config["preferences"]["exploration"]["keep"]:
        keymaps.append(generate_random_keymap(keymap, corpus["char"]))

    keymaps = search_for_best_keymap(keymaps, corpus["char"], config)

    print()
    print(len(keymaps), "keymap generated")
    for keymap in keymaps:
        KeymapHelper.save(keymap)
        KeymapHelper.print(keymap)
        print(f"Score: {keymap.score}\n\n")
    print(len(keymaps), "keymap generated")
    return


def search_for_best_keymap(
    keymaps: list[Keymap], chars: list[str], config: dict
) -> list[Keymap]:
    known_keymaps: set[str] = set()
    start_time = time.time()
    for i in range(0, config["preferences"]["exploration"]["generations"]):
        print(f"[{i+1}] ", end="", flush=True)
        # Create a new generation
        create_next_generation(keymaps, known_keymaps, chars, config)
        for keymap in keymaps:
            known_keymaps.add(KeymapHelper.get_hash(keymap))
        # Keep best keymaps
        keymaps = sorted(keymaps, key=lambda x: x.score)[
            : config["preferences"]["exploration"]["keep"]
        ]
        print(f"Best score: {keymaps[0].score}")
        KeymapHelper.print(keymaps[0])
        print()
    runtime = time.time() - start_time
    print(f"{len(known_keymaps) / runtime}keyboards/s [{len(known_keymaps)}]")
    return list(reversed(keymaps))[:20]


def generate_random_keymap(keymap: Keymap, chars: list[str]) -> Keymap:
    chars = list(chars)
    random.shuffle(chars)
    keymap = KeymapHelper.copy(keymap)
    for index in keymap.free_keys:
        keymap = KeymapHelper.assign_char_to_key(
            keymap, chars.pop(), keymap.keys[index]
        )
        if not chars:
            break
    # Calculate the score
    score = Calculator.get().get_score(keymap)
    keymap = KeymapHelper.set_score(keymap, score)
    # KeymapHelper.print(keymap)
    # print()
    return keymap


def create_next_generation(
    keymaps: list[Keymap], known_keymaps: list[Keymap], chars: list[str], config: dict
) -> None:
    size = len(keymaps)
    while len(keymaps) < config["preferences"]["exploration"]["population"]:
        # Choose 2 keymaps at random
        keymap1 = random.choice(keymaps[:size])
        keymap2 = keymap1
        while keymap2 == keymap1:
            keymap2 = random.choice(keymaps[:size])
        # Find all the chars on the right hand side of the first keymap
        # ordered by their score on the second keymap.
        chars = [
            k.char
            for k in sorted(
                keymap1.keys,
                key=lambda x: KeymapHelper.get_key(keymap2, x.fingering).score,
            )
            if k.fingering.hand == "right" and k.char in chars
        ]
        keymap = KeymapHelper.copy(keymap1)
        # Add the missing letters based to the first keymap
        for layer in keymap.definition["layers"]:
            for row in keymap.definition["rows"]:
                for column in keymap.definition["columns"]["right"]:
                    if not chars:
                        break
                    key = KeymapHelper.get_key(
                        keymap, Fingering(layer, row, "right", column)
                    )
                    if key is not None and not key.locked:
                        keymap = KeymapHelper.assign_char_to_key(
                            keymap,
                            chars.pop(),
                            key,
                        )
        # Add random mutations
        for _ in range(0, len(keymap.mapping.keys())):
            if (
                random.randint(1, 100)
                <= config["preferences"]["exploration"]["mutation_rate"]
            ):
                key1 = random.choice(keymap.keys)
                key2 = random.choice(keymap.keys)
                if key1.locked is False and key2.locked is False:
                    keymap = KeymapHelper.assign_char_to_key(keymap, key2.char, key1)
                    keymap = KeymapHelper.assign_char_to_key(keymap, key1.char, key2)

        if KeymapHelper.get_hash(keymap) not in known_keymaps:
            # Calculate the score
            score = Calculator.get().get_score(keymap)
            keymap = KeymapHelper.set_score(keymap, score)

            keymaps.append(keymap)
