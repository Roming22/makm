"""Score a keyboard layout"""
# import time
import typing

from keyboard import Keyboard


def get_score(
    keyboard: Keyboard, missing_chars: list, corpus: dict, config: dict
) -> typing.Tuple[float, float]:
    """The approach lacks in finess, as the score is recalculated
    from scratch everytime.
    Maybe this could be optimized so that knowing the latest score and
    the new key, only the delta is recomputed?"""
    base_score = get_base_score(keyboard, corpus, config)
    best_score = (
        get_best_score_lower_bound(keyboard, missing_chars, corpus, config) + base_score
    )
    worst_score = (
        get_worst_score_upper_bound(keyboard, missing_chars, corpus, config)
        + base_score
    )
    # print(best_score, worst_score)
    # time.sleep(0.001)
    return best_score, worst_score


def get_base_score(keyboard: Keyboard, corpus: dict, config: dict) -> float:
    """Score with the populated keys"""
    score = 0.0
    for char in keyboard.get_chars().values():
        if char is not None and char.key is not None:
            score += char.score * char.key.score
        # score += get_ngram_score(
        #     key,
        #     char,
        #     keyboard,
        #     corpus["bigram_count"],
        #     config["preferences"]["score"]["rolls"]["bigram"],
        # )
        # score += get_trigram_score(
        #     key,
        #     char,
        #     keyboard,
        #     corpus["trigram_count"],
        #     config["preferences"]["score"]["rolls"]["trigram"],
        # )
    return score


# def get_ngram_score(
#     key: tuple, char: str, keyboard: dict, ngrams: dict, bonus: float, best=False
# ) -> float:
#     roll_keys = get_roll_keys(key, len(ngrams) - 1)
#     for ng, count in ngrams.items():
#         print(ng)
#         if ng.startswith(char):
#             print(char, ng, key)
#             perfect_match = True
#             impossible_match = False

#             for roll in roll_keys:
#                 if keyboard[roll_key] == next_char or (
#                     keyboard[roll_key] is None and best
#                 ):
#                     return bonus * count
#     return 0


def get_best_score_lower_bound(
    keyboard: Keyboard, missing_chars: list, corpus: dict, config: dict
) -> float:
    """This score must be equal or lower than the final score"""
    score = 0.0
    return score


def get_worst_score_upper_bound(
    keyboard: Keyboard, missing_chars: list, corpus: dict, config: dict
) -> float:
    """This score must be equal or greater than the final score"""
    score = 0.0
    return score
