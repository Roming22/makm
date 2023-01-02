"""Generate keyboard layouts"""
import random

import layout_calculator
from keyboard import Char, Keyboard


def generate(corpus: dict, config: dict):
    for rows in config["keyboard"]["constraints"].values():
        for hands in rows.values():
            for fingers in hands.values():
                for finger, char in fingers.items():
                    try:
                        fingers[finger] = (char, corpus["letter_count"].pop(char))
                    except:
                        fingers[finger] = (char, 0)
    keyboard = Keyboard(config["keyboard"])
    keyboard.print("heat")
    corpus_chars = [
        Char(c, v)
        for c, v in sorted(corpus["letter_count"].items(), key=lambda x: x[1])
    ]
    keyboard_tree = {
        "char": "root",
        "key": "root",
        "keyboard": keyboard,
        "worst_score": None,
        "best_score": None,
        "missing_chars": corpus_chars,
        "nodes": [],
        "parent": None,
        "progress": 0,
    }
    search_for_best_keyboard(keyboard_tree, corpus, config)
    keyboards = keyboardtree_to_keyboards(keyboard_tree)
    print(len(keyboards), "keyboard generated")
    for keyboard in keyboards:
        keyboard.print()
    print(len(keyboards), "keyboard generated")
    return


def search_for_best_keyboard(node: dict, corpus: dict, config: dict):
    if not node["missing_chars"]:
        if random.randint(1, 10) == 10:
            display_progress(node)
        # print("No more keys :)")
        return

    add_key_to_keyboard_tree(node, corpus, config)
    remove_deadends(node)
    for child in node["nodes"]:
        node["progress"] += 1
        search_for_best_keyboard(child, corpus, config)


def add_key_to_keyboard_tree(node: dict, corpus: dict, config: dict) -> None:
    char = node["missing_chars"][-1]
    free_keys = node["keyboard"].get_free_keys()
    if not free_keys:
        raise Exception("Not enough keys")
    for key in free_keys:
        child = {
            "char": char.char,
            "key": (key.layer, *key.fingering),
            "keyboard": node["keyboard"].copy(),
            "worst_score": None,
            "best_score": None,
            "missing_chars": node["missing_chars"][:-1],
            "nodes": [],
            "parent": node,
            "progress": 0,
        }
        child["keyboard"].assign_char_to_key(char, key)
        if len(child["keyboard"].get_free_keys()) != len(free_keys) - 1:
            raise Exception("Bad object management")
        child["best_score"], child["worst_score"] = layout_calculator.get_score(
            child["keyboard"], child["missing_chars"], corpus, config
        )
        node["nodes"].append(child)


def remove_deadends(node: dict) -> None:
    best_score = min([n["best_score"] for n in node["nodes"]])
    # print("bestscore for", node["char"], ":", best_score)
    remove = []
    for child in node["nodes"]:
        if child["worst_score"] > best_score:
            remove.append(child)
    for child in remove:
        # print("Deadend:", child["key"])
        node["nodes"].remove(child)
    # time.sleep(3)


def display_progress(node: dict) -> None:
    progress = []
    parent = node["parent"]
    while parent:
        progress.append(
            # f"{parent['nodes'][0]['char']}: {parent['progress']}/{len(parent['nodes'])}"
            f"{parent['progress']}/{len(parent['nodes'])}"
        )
        parent = parent["parent"]
    print("-".join(reversed(progress)))


def keyboardtree_to_keyboards(node: dict) -> list:
    keyboards = []
    nodes = [node]
    while nodes:
        new_nodes = []
        for nd in nodes:
            new_nodes += nd["nodes"]
        if not nd["missing_chars"]:
            keyboards.append(nd["keyboard"])
        nodes = new_nodes

    return keyboards
