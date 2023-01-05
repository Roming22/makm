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
        "missing_chars": corpus_chars[-13:],
    }

    start_time = time.time()
    results = search_for_best_keymap(keymap_tree)
    runtime = time.time() - start_time

    print()
    print(len(results), "keymap generated")
    for node in results:
        KeymapHelper.print(node["keymap"])
        print("best:", node["best_score"], "    worst:", node["worst_score"], "\n\n")
    print(len(results), "keymap generated")
    print(KeymapHelper.count / runtime, "keyboards/s")
    return


def search_for_best_keymap(node: dict) -> list:
    nodes = [node]
    count = 0
    while nodes:
        new_nodes = []
        while nodes:
            if not nodes[0]["missing_chars"]:
                print("results", len(nodes))
                nodes = sorted(nodes, key=lambda x: x["best_score"], reverse=True)
                return nodes
            node = nodes.pop(0)
            new_nodes.extend(add_key_to_keymap_tree(node))
            count += 1
            if count > 1000:
                count = 0
                new_nodes = remove_deadends(
                    {
                        "nodes": new_nodes,
                        "best_score": node["best_score"],
                        "worst_score": node["worst_score"],
                    }
                )
        print(new_nodes[0]["char"], "", end="")
        nodes = remove_deadends(
            {
                "nodes": new_nodes,
                "best_score": node["best_score"],
                "worst_score": node["worst_score"],
            }
        )
        print(len(nodes))


def add_key_to_keymap_tree(node: dict) -> list:
    char = node["missing_chars"][-1]
    free_keys = KeymapHelper.get_free_keys(node["keymap"])
    if not free_keys:
        raise Exception("Not enough keys")
    nodes = []
    for key in free_keys[:6]:
        child = {
            "char": char.char,
            "key": key.fingering,
            "keymap": KeymapHelper.assign_char_to_key(node["keymap"], char, key),
            "worst_score": None,
            "best_score": None,
            "missing_chars": node["missing_chars"][:-1],
        }
        key = KeymapHelper.get_key(child["keymap"], key.fingering)
        child["best_score"], child["worst_score"] = Calculator.get().get_score_for_key(
            key, child["keymap"], child["missing_chars"]
        )
        nodes.append(child)
    return nodes


def remove_deadends(node: dict) -> list:
    best_score = get_best_score(node)
    worst_score = get_worst_score(node)
    keep = []
    while node["nodes"]:
        child = node["nodes"].pop()
        if child["best_score"] <= worst_score:
            keep.append(child)
    return keep


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
