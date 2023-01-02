"""Generate keyboard layouts"""
import random
import time

from keyboard import Char, Keyboard
from layout_calculator import Calculator


def generate(corpus: dict, config: dict):
    # Add constraints to keyboard layout
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
    Calculator.get().set(corpus, config)
    corpus_chars = [
        Char(c, v)
        for c, v in sorted(corpus["letter_count"].items(), key=lambda x: x[1])[-6:]
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
    start_time = time.time()
    search_for_best_keyboard(keyboard_tree)
    runtime = time.time() - start_time
    keyboards = keyboardtree_to_keyboards(keyboard_tree)
    print(len(keyboards), "keyboard generated")
    for keyboard in keyboards:
        keyboard.print()
    print(Keyboard.count / runtime, "keyboards/s")
    return


def search_for_best_keyboard(node: dict):
    print(".", end="", flush=True)
    if not node["missing_chars"]:
        print()
        display_progress(node)
        return

    add_key_to_keyboard_tree(node)
    remove_deadends(node)
    for child in node["nodes"]:
        node["progress"] += 1
        search_for_best_keyboard(child)


def add_key_to_keyboard_tree(node: dict) -> None:
    char = node["missing_chars"][-1]
    free_keys = node["keyboard"].get_free_keys()
    if not free_keys:
        raise Exception("Not enough keys")
    for key in free_keys[:5]:
        child = {
            "char": char.char,
            "key": (key.layer.name, *key.fingering),
            "keyboard": node["keyboard"].copy(),
            "worst_score": None,
            "best_score": None,
            "missing_chars": node["missing_chars"][:-1],
            "nodes": [],
            "parent": node,
            "progress": 0,
        }
        child_key = child["keyboard"].assign_char_to_key(char, key)
        if len(child["keyboard"].get_free_keys()) != len(free_keys) - 1:
            raise Exception("Bad object management")
        child["best_score"], child["worst_score"] = Calculator.get().get_score_for_key(
            child_key, child["keyboard"], child["missing_chars"]
        )
        node["nodes"].append(child)


def remove_deadends(node: dict) -> None:
    worst_score = min([n["worst_score"] for n in node["nodes"]])
    if node["worst_score"] is not None:
        worst_score = min(worst_score, node["worst_score"])
    remove = []
    for child in node["nodes"]:
        # print(child["char"], child["key"], child["best_score"], child["worst_score"])
        if child["best_score"] > worst_score:
            remove.append(child)
    time.sleep(2)
    for child in remove:
        # print("Deadend:", child["key"])
        node["nodes"].remove(child)
    # time.sleep(3)


def display_progress(node: dict) -> None:
    progress = []
    parent = node["parent"]
    while parent:
        progress.append(f"{parent['progress']}/{len(parent['nodes'])}")
        parent = parent["parent"]
    print("-".join(reversed(progress)), end="", flush=True)


def keyboardtree_to_keyboards(node: dict) -> list:
    keyboards = []
    nodes = [node]
    while nodes:
        new_nodes = []
        for nd in nodes:
            new_nodes += nd["nodes"]
        if not nd["missing_chars"]:
            print("keyboard score:", nd["best_score"], nd["worst_score"])
            keyboards.append(nd["keyboard"])
        nodes = new_nodes

    return keyboards
