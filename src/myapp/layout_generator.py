"""Generate keyboard layouts"""
import copy
import typing


def generate(corpus: dict, config:dict):
    heatmap = sorted(generate_heatmap(config)[".keys"].items(), key=lambda x:x[1], reverse=True)
    print(heatmap)
    keys = corpus["letter_count"]
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

# def add_key_to_layout(keys: list[str], layout: list) -> typing.Iterator[list]:
#     if keys:
#         _keys = list(keys)
#         _k = keys.pop
#         _layout = list(layout)
#     else:
#         return
#     for _r in _layout:
#         for _c in _r:
#             if not _layout[_r][_c]:
#                 _layout[_r][_c] = _k
#                 yield add_key_to_layout(_keys, _layout)