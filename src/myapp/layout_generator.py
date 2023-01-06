"""Generate keymap layouts"""
import time

from keyboard import Char, KeymapHelper
from layout_calculator import Calculator


def generate(corpus: dict, config: dict):
    corpus_chars = [
        Char(c, v)
        for c, v in sorted(
            corpus["letter_count"].items(), key=lambda x: x[1], reverse=True
        )
    ]
    keymap = KeymapHelper.new(config["keyboard"])
    print()
    KeymapHelper.print(keymap, "score")
    keymap = KeymapHelper.add_constraints_to_keymap(
        config["keyboard"]["constraints"], corpus_chars, keymap
    )
    print()
    KeymapHelper.print(keymap)

    print([c.char for c in corpus_chars])
    Calculator.get().set(corpus, config)
    keymap_tree = {
        "base_score": 0,
        "char": "root",
        "key": "root",
        "keymap": keymap,
        "lower_score_limit": None,
        "missing_chars": corpus_chars[:11],
        "upper_score_limit": None,
    }

    start_time = time.time()
    results = search_for_best_keymap(keymap_tree)
    runtime = time.time() - start_time

    print()
    print(len(results), "keymap generated")
    for node in results:
        KeymapHelper.print(node["keymap"])
        print(
            "best:",
            node["lower_score_limit"],
            "    worst:",
            node["upper_score_limit"],
            "\n\n",
        )
    print(len(results), "keymap generated")
    print(KeymapHelper.count / runtime, "keyboards/s")
    return


def search_for_best_keymap(node: dict) -> list:
    nodes = [node]
    while nodes:
        new_nodes = []
        if nodes[0]["missing_chars"]:
            print(nodes[0]["missing_chars"][0].char, end=": ", flush=True)
        for node in nodes:
            if not nodes[0]["missing_chars"]:
                print("results", len(nodes))
                sorted(nodes, key=lambda x: x["upper_score_limit"], reverse=True)
                return nodes
            if not ScoreChecker.is_deprecated(node):
                new_nodes.extend(add_key_to_keymap_tree(node))
        print(len(new_nodes))
        nodes = new_nodes
    raise Exception("Bad Omen")


def add_key_to_keymap_tree(node: dict) -> list:
    char = node["missing_chars"][0]
    free_keys = [node["keymap"].keys[f] for f in node["keymap"].free_keys[:6]]
    if not free_keys:
        raise Exception("Not enough keys")
    nodes = []
    for key in free_keys[:8]:
        child = {
            "base_score": node["base_score"],
            "char": char.char,
            "key": key.fingering,
            "keymap": KeymapHelper.assign_char_to_key(node["keymap"], char, key),
            "lower_score_limit": node["base_score"],
            "upper_score_limit": node["base_score"],
            "missing_chars": node["missing_chars"][1:],
        }
        key = KeymapHelper.get_key(child["keymap"], key.fingering)
        (
            base_score,
            lower_score_limit,
            upper_score_limit,
        ) = Calculator.get().get_score_for_key(
            key, child["keymap"], child["missing_chars"]
        )
        child["base_score"] += base_score
        child["lower_score_limit"] += lower_score_limit
        child["upper_score_limit"] += upper_score_limit
        if not ScoreChecker.is_deprecated(child):
            ScoreChecker.check(child)
            nodes.append(child)
    return nodes


class ScoreChecker:
    lower_score_node: dict = None
    upper_score_node: dict = None

    @classmethod
    def check(cls, node) -> float:
        # if cls.lower_score_node:
        #     print("OVERALL UPPER:", cls.upper_score_node["upper_score_limit"])
        #     print("NODE UPPER:", node["upper_score_limit"])

        if cls.lower_score_node is None:
            cls.lower_score_node = node
        elif cls.lower_score_node["lower_score_limit"] < node["lower_score_limit"]:
            cls.lower_score_node = node

        # print("RESULT UPPER:", cls.upper_score_node["upper_score_limit"])
        # print()

        return not cls.is_deprecated(node)

    @classmethod
    def is_deprecated(cls, node) -> bool:
        if cls.lower_score_node is None:
            return False
        # print(">", node["upper_score_limit"])
        return node["upper_score_limit"] < cls.lower_score_node["lower_score_limit"]


ScoreChecker.lower_score_node
