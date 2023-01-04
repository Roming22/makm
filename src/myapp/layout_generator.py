"""Generate keymap layouts"""
import time

from keyboard import Char, KeymapHelper
from layout_calculator import Calculator


def generate(corpus: dict, config: dict):
    corpus_chars = [
        Char(c, v)
        for c, v in sorted(corpus["letter_count"].items(), key=lambda x: x[1])
    ]
    keymap = KeymapHelper.new(config["keyboard"])
    print()
    KeymapHelper.print(keymap, "score")
    keymap = KeymapHelper.add_constraints_to_keymap(
        config["keyboard"]["constraints"], corpus_chars, keymap
    )
    KeymapHelper.print(keymap)
    print()

    Calculator.get().set(corpus, config)
    keymap_tree = {
        "char": "root",
        "key": "root",
        "keymap": keymap,
        "worst_score": None,
        "best_score": None,
        "missing_chars": corpus_chars[-11:],
        "nodes": [],
        "parent": None,
        "progress": 0,
    }

    start_time = time.time()
    search_for_best_keymap(keymap_tree)
    runtime = time.time() - start_time

    results = keymaptree_to_results(keymap_tree)
    print()
    print(len(results), "keymap generated")
    for node in results:
        KeymapHelper.print(node["keymap"])
        print("best:", node["best_score"], "    worst:", node["worst_score"], "\n\n")
    print(len(results), "keymap generated")
    print(KeymapHelper.count / runtime, "keyboards/s")
    return


def search_for_best_keymap(node: dict):
    nodes = [node]
    while nodes:
        new_nodes = []
        for node in nodes:
            if not node["missing_chars"]:
                return
            add_key_to_keymap_tree(node)
            new_nodes.extend(node["nodes"])
        print(new_nodes[0]["char"], "", end="")
        remove_deadends(
            {
                "nodes": new_nodes,
                "best_score": node["best_score"],
                "worst_score": node["worst_score"],
            }
        )
        print(len(new_nodes))
        nodes = new_nodes


def add_key_to_keymap_tree(node: dict) -> None:
    char = node["missing_chars"][-1]
    free_keys = KeymapHelper.get_free_keys(node["keymap"])
    if not free_keys:
        raise Exception("Not enough keys")
    for key in free_keys[:5]:
        child = {
            "char": char.char,
            "key": key.fingering,
            "keymap": KeymapHelper.assign_char_to_key(node["keymap"], char, key),
            "worst_score": None,
            "best_score": None,
            "missing_chars": node["missing_chars"][:-1],
            "nodes": [],
            "parent": node,
            "progress": 0,
        }
        key = KeymapHelper.get_key(child["keymap"], key.fingering)
        child["best_score"], child["worst_score"] = Calculator.get().get_score_for_key(
            key, child["keymap"], child["missing_chars"]
        )
        node["nodes"].append(child)


def remove_deadends(node: dict) -> None:
    best_score = get_best_score(node)
    worst_score = get_worst_score(node)
    remove = []
    for child in node["nodes"]:
        if child["best_score"] and child["best_score"] > worst_score:
            remove.append(child)
    for child in remove:
        node["nodes"].remove(child)
        # node["best_score"] = best_score
        # node["worst_score"] = worst_score
        # print(node["char"], len(node["nodes"]))
        # node = node["parent"]


def get_best_score(node: dict) -> float:
    score = max([n["best_score"] for n in node["nodes"] if n["best_score"] is not None])
    if node["best_score"] is not None:
        if score > node["best_score"]:
            raise Exception("Best score should only increase")
        score = min(score, node["best_score"])
    return score


def get_worst_score(node: dict) -> float:
    score = min([n["worst_score"] for n in node["nodes"]])
    if node["worst_score"] is not None:
        if score > node["best_score"]:
            raise Exception("Worst score should only decrease")
        score = min(score, node["worst_score"])
    return score


def display_progress(node: dict) -> None:
    progress = []
    parent = node["parent"]
    while parent:
        progress.append(f"{parent['progress']}/{len(parent['nodes'])}")
        parent = parent["parent"]
    print("-".join(reversed(progress)), end="", flush=True)


def keymaptree_to_results(node: dict) -> list:
    results = []
    nodes = []
    while node:
        if node["missing_chars"]:
            nodes += node["nodes"]
        else:
            results.append(node)
        if nodes:
            node = nodes.pop()
        else:
            node = False
    results = sorted(results, key=lambda x: x["best_score"], reverse=True)
    return results
