"""Score a keyboard layout"""
# import time
import typing


def get_score(
    keymap: dict, missing_keys: list, corpus: dict, config: dict
) -> typing.Tuple[float, float]:
    """The approach lacks in finess, as the score is recalculated
    from scratch everytime.
    Maybe this could be optimized so that knowing the latest score and
    the new key, only the delta is recomputed?"""
    base_score = get_base_score(keymap, corpus, config)
    best_score = (
        get_best_score_lower_bound(keymap, missing_keys, corpus, config) + base_score
    )
    worst_score = (
        get_worst_score_upper_bound(keymap, missing_keys, corpus, config) + base_score
    )
    # print(best_score, worst_score)
    # time.sleep(0.001)
    return best_score, worst_score


def get_base_score(keymap: dict, corpus: dict, config: dict) -> float:
    """Score with the populated keys"""
    score = 0.0
    for key in keymap.values():
        char = key["key"]
        if char:
            score += key["heat"] * key["score"]
    return score


def get_best_score_lower_bound(
    keymap: dict, missing_keys: list, corpus: dict, config: dict
) -> float:
    """This score must be equal or lower than the final score"""
    score = 0.0
    return score


def get_worst_score_upper_bound(
    keymap: dict, missing_keys: list, corpus: dict, config: dict
) -> float:
    """This score must be equal or greater than the final score"""
    score = 0.0
    return score
