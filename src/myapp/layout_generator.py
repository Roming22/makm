"""Generate keyboard layouts"""
import copy

import layout_calculator


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
        "worst_score": None,
        "best_score": None,
        "missing_keys": sorted(corpus["letter_count"].items(), key=lambda x: x[1]),
        "nodes": [],
        "parent": None,
        "progress": 0,
    }
    search_for_best_keymap(keymap_tree, corpus, config)
    keyboards = keymaptree_to_keyboards(keymap_tree)
    for keyboard in enumerate(keyboards):
        print_keyboard(keyboard)
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
                    print(
                        f"[{keyboard.get(layer,{}).get(row,{}).get(hand,{}).get(finger,' ')}]",
                        end="",
                    )
                print(" | ", end="")
            print()


def search_for_best_keymap(keymap_tree: dict, corpus: dict, config: dict):
    if not keymap_tree["missing_keys"]:
        # print("No more keys :)")
        return

    add_key_to_keymap_tree(keymap_tree, corpus, config)
    remove_deadends(keymap_tree)
    for node in keymap_tree["nodes"]:
        keymap_tree["progress"] += 1
        display_progress(node)
        search_for_best_keymap(node, corpus, config)


def add_key_to_keymap_tree(node: dict, corpus: dict, config: dict) -> None:
    key = node["missing_keys"][-1]
    for _key in node["heatmap"]:
        child = {
            "heatmap": copy.deepcopy(node["heatmap"]),
            "heatkey": _key,
            "key": {"heat": _key[1], "key": key[0], "score": key[1]},
            "keymap": copy.deepcopy(node["keymap"]),
            "worst_score": None,
            "best_score": None,
            "missing_keys": node["missing_keys"][:-1],
            "nodes": [],
            "parent": node,
            "progress": 0,
        }
        child["keymap"][_key] = child["key"]
        child["heatmap"].remove(_key)
        child["best_score"], child["worst_score"] = layout_calculator.get_score(
            child["keymap"], child["missing_keys"], corpus, config
        )
        # print(key, _key)
        node["nodes"].append(child)


def remove_deadends(node: dict) -> None:
    best_score = min([n["best_score"] for n in node["nodes"]])
    remove = []
    for child in node["nodes"]:
        if child["worst_score"] > best_score:
            remove.append(child)
    for child in remove:
        # print("Deadend:", child["key"], child["heatkey"])
        node["nodes"].remove(child)


def display_progress(node: dict) -> None:
    progress = [f"[{len(node['missing_keys'])}]"]
    while node["parent"]:
        progress.append(f"{node['progress']}/{len(node['nodes'])}")
        node = node["parent"]
    progress.append(f"{node['progress']}/{len(node['nodes'])}")
    print(" - ".join(reversed(progress)))


def keymaptree_to_keyboards(node: dict) -> list:
    keyboards = []

    return keyboards
