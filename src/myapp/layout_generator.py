"""Generate keyboard layouts"""
import copy
import typing


def generate(corpus: dict, config:dict):
    heatmap = sorted(generate_heatmap(config)[".keys"].items(), key=lambda x:x[1], reverse=True)
    print(heatmap)
    keymap = {k: {
        "heat": v,
        "key": None,
        "score": None
     } for k,v in heatmap}
    keymap_tree = {
        "heatmap": heatmap,
        "key": "root",
        "keymap": keymap,
        "max_score": None,
        "min_score": None,
        "nodes": [],
        "parent": None,
        "score": None,
        "todo": sorted(corpus["letter_count"].items(), key=lambda x:x[1]),
    }
    search_for_best_keymap(keymap_tree, corpus)
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

def generate_heatmap(config:dict) -> dict:
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

def search_for_best_keymap(keymap_tree: dict, corpus:dict):
    if not keymap_tree["todo"]:
        return

    add_key_to_keymap_tree(keymap_tree)
    # update_score(keymap_tree, config)
    # prune_deadends(keymap_tree)
    for node in keymap_tree["nodes"]:
        search_for_best_keymap(node, corpus)

def add_key_to_keymap_tree(parent:dict) -> None:
    key = parent["todo"][-1]
    print(key)
    for _key in parent["heatmap"]:
        new_node = {
        "heatmap": copy.deepcopy(parent["heatmap"]),
        "key": key[0],
        "keymap": copy.deepcopy(parent["keymap"]),
        "max_score": None,
        "min_score": None,
        "nodes": [],
        "parent": parent,
        "score": key[1],
        "todo": parent["todo"][:-1],
    }
        print(_key)
        new_node["heatmap"].remove(_key)
        # new_node["keymap"]["key"] = _key
        new_node["todo"] = []
        parent["nodes"].append(new_node)
