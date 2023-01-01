"""Generate keyboard layouts"""
import copy
import random

random.seed("test")


def generate(corpus: dict, config: dict):
    heatmap = sorted(
        generate_heatmap(config)[".keys"].items(), key=lambda x: x[1], reverse=True
    )
    print(heatmap)
    keymap = {k: {"heat": v, "key": None, "score": None} for k, v in heatmap}
    keymap_tree = {
        "heatmap": heatmap,
        "key": "root",
        "keymap": keymap,
        "max_score": None,
        "min_score": None,
        "missing_keys": sorted(corpus["letter_count"].items(), key=lambda x: x[1]),
        "nodes": [],
        "parent": None,
        "progress": 0,
        "score": None,
    }
    search_for_best_keymap(keymap_tree, corpus, config)
    # keyboard = keymap_to_keyboard(keymap)
    # print_keyboard(keyboard)
    return


def generate_keyboard_layout(config: dict) -> dict:
    layout = {
        ".layout": config,
    }
    for layer in config["layers"]:
        layout[layer] = {}
        for row, hands in config["rows"].items():
            layout[layer][row] = {}
            for hand, fingers in hands.items():
                layout[layer][row][hand] = {f: "" for f in fingers}
    return layout


def generate_heatmap(config: dict) -> dict:
    layout = config["keyboard"]["layout"]
    heatmap = generate_keyboard_layout(layout)
    heatmap[".name"] = "Heatmap"
    heatmap[".keys"] = {}
    score = config["keyboard"]["score"]
    for layer, rows in heatmap.items():
        if layer not in layout["layers"]:
            continue
        for row, hands in rows.items():
            for hand, fingers in hands.items():
                for finger in fingers.keys():
                    heat = score["layers"][layer]
                    heat += score["rows"][row]
                    heat += score["fingers"][hand][finger]
                    heatmap[layer][row][hand][finger] = heat
                    heatmap[".keys"][(layer, row, hand, finger)] = heat
    return heatmap


def print_keyboard(keyboard: dict) -> None:
    print()
    print(f"# {keyboard.get('.name', 'Keyboard')}")
    layout = keyboard[".layout"]
    for layer in layout["layers"]:
        print()
        print(f"## {layer}")
        for row, hands in layout["rows"].items():
            for hand, fingers in hands.items():
                for finger in fingers:
                    print(f"[{keyboard[layer][row][hand][finger]}]", end="")
                print(" | ", end="")
            print()


def search_for_best_keymap(keymap_tree: dict, corpus: dict, config: dict):
    if not keymap_tree["missing_keys"]:
        print("No more keys :)")
        return

    add_key_to_keymap_tree(keymap_tree)
    remove_deadends(keymap_tree)
    for node in keymap_tree["nodes"]:
        keymap_tree["progress"] += 1
        display_progress(node)
        search_for_best_keymap(node, corpus, config)


def add_key_to_keymap_tree(node: dict) -> None:
    key = node["missing_keys"][-1]
    for _key in node["heatmap"]:
        child = {
            "heatmap": copy.deepcopy(node["heatmap"]),
            "heatkey": _key,
            "key": key[0],
            "keymap": copy.deepcopy(node["keymap"]),
            "max_score": None,
            "min_score": None,
            "missing_keys": node["missing_keys"][:-1],
            "nodes": [],
            "parent": node,
            "progress": 0,
            "score": key[1],
        }
        child["heatmap"].remove(_key)
        child["min_score"] = random.randint(0, 100)
        child["max_score"] = child["min_score"] + random.randint(0, 40)
        print(key, _key)
        node["nodes"].append(child)


def remove_deadends(node: dict) -> None:
    min_score = max([n["min_score"] for n in node["nodes"]])
    remove = []
    for child in node["nodes"]:
        if child["max_score"] < min_score:
            remove.append(child)
    for child in remove:
        print("Deadend:", child["key"], child["heatkey"])
        node["nodes"].remove(child)


def display_progress(node: dict) -> None:
    progress = []
    while node["parent"]:
        progress.append(f"{node['progress']}/{len(node['nodes'])}")
        node = node["parent"]
    progress.append(f"{node['progress']}/{len(node['nodes'])}")
    print(" / ".join(reversed(progress)))
