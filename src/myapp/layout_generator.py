"""Generate keymap layouts"""
import time

from myapp.keyboard import Char, KeymapHelper
from myapp.layout_calculator import Calculator


def generate(corpus: dict, config: dict):
    # Limit corpus for tests
    corpus["char"] = {
        k: v
        for k, v in list(
            sorted(list(corpus["char"].items()), key=lambda x: x[1], reverse=True)
        )[:18]
    }
    remove = []
    for char in corpus["bigram"].keys():
        if char not in corpus["char"].keys():
            remove.append(char)
    for char in remove:
        corpus["bigram"].pop(char)
    for char1 in corpus["bigram"].keys():
        remove = []
        for char2 in corpus["bigram"][char1].keys():
            if char2 not in corpus["char"].keys():
                remove.append(char2)
        for char in remove:
            try:
                corpus["bigram"][char1].pop(char2)
            except KeyError:
                pass
    corpus_chars = [
        Char(c, 1 + v)
        for c, v in sorted(corpus["char"].items(), key=lambda x: x[1], reverse=True)
    ]
    Calculator.get().set(corpus, config)
    keymap = KeymapHelper.new(config["keyboard"])
    print()
    KeymapHelper.print(keymap, "score")
    keymap = KeymapHelper.add_constraints_to_keymap(
        config["keyboard"]["constraints"], corpus_chars, keymap
    )
    print()
    KeymapHelper.print(keymap)

    print([c.char for c in corpus_chars])
    keymap_tree = {
        "base_score": 0,
        "char": "root",
        "exploration": config["preferences"]["exploration"],
        "key": "root",
        "keymap": keymap,
        "lower_score_limit": None,
        "missing_chars": corpus_chars,
        "upper_score_limit": None,
    }

    start_time = time.time()
    results = search_for_best_keymap(keymap_tree)
    runtime = time.time() - start_time

    print()
    print(len(results), "keymap generated")
    for node in results:
        KeymapHelper.save(node["keymap"])
        KeymapHelper.print(node["keymap"])
        print(
            "Score:",
            node["lower_score_limit"],
            "\n\n",
        )
    print(len(results), "keymap generated")
    print(KeymapHelper.count / runtime, "keyboards/s")
    return


def search_for_best_keymap(node: dict) -> list:
    nodes = [node]
    count = 0
    total = len(nodes[0]["missing_chars"])
    while nodes:
        if not nodes[0]["missing_chars"]:
            print("results", len(nodes))
            sorted(nodes, key=lambda x: x["upper_score_limit"], reverse=True)
            return nodes

        count += 1
        print(
            f"[{count}/{total}]",
            nodes[0]["missing_chars"][0].char,
            end=": ",
            flush=True,
        )
        new_nodes = []
        for node in nodes:
            if not ScoreChecker.is_deprecated(node):
                new_nodes.extend(add_key_to_keymap_tree(node))
        print(len(new_nodes))
        nodes = new_nodes
        ScoreChecker.reset()
    raise Exception("Bad Omen")


def add_key_to_keymap_tree(node: dict) -> list:
    char = node["missing_chars"][0]
    free_keys = [node["keymap"].keys[f] for f in node["keymap"].free_keys]
    if not free_keys:
        raise Exception("Not enough keys")
    nodes = []
    for key in free_keys[: node["exploration"]["max_keys"]]:
        new_keymap = KeymapHelper.assign_char_to_key(node["keymap"], char, key)
        child = {
            "base_score": node["base_score"],
            "char": char.char,
            "exploration": node["exploration"],
            "key": key.fingering,
            "keymap": new_keymap,
            "lower_score_limit": node["base_score"],
            "missing_chars": node["missing_chars"][1:],
            "upper_score_limit": node["base_score"],
        }
        key = KeymapHelper.get_key(child["keymap"], key.fingering)
        (
            base_score,
            lower_score_limit,
            upper_score_limit,
        ) = Calculator.get().get_score_for_key(
            key,
            child["keymap"],
            child["missing_chars"][: node["exploration"]["rolling_window"]],
        )
        child["base_score"] += base_score
        child["lower_score_limit"] += lower_score_limit
        child["upper_score_limit"] += upper_score_limit
        if ScoreChecker.check(child):
            nodes.append(child)
    return nodes


class ScoreChecker:
    upper_score_node: dict = {}

    @classmethod
    def check(cls, node) -> float:
        if (
            not cls.upper_score_node
            or cls.upper_score_node["upper_score_limit"] > node["upper_score_limit"]
        ):
            cls.upper_score_node = node
        return not cls.is_deprecated(node)

    @classmethod
    def is_deprecated(cls, node) -> bool:
        if not cls.upper_score_node:
            return False
        return node["lower_score_limit"] > cls.upper_score_node["upper_score_limit"]

    @classmethod
    def reset(cls) -> None:
        cls.upper_score_node = {}
