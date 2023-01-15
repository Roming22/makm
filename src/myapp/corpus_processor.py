"""Generate input data from the corpus"""
import glob
import os
import random

import git
import yaml

# Make output reproducable
random.seed("makm")


def generate_data(corpus_preferences: dict) -> dict:

    language_weight = {}
    for languages in corpus_preferences.values():
        for language, data in languages.items():
            language_weight[language] = data["weight"]
    total_weight = sum(language_weight.values())
    language_weight = {k: v / total_weight for k, v in language_weight.items()}

    language_data = {}
    language_data.update(generate_i18_data(corpus_preferences["i18n"]))
    language_data.update(generate_code_data(corpus_preferences["code"]))
    corpus_data = consolidate_data(language_data, language_weight)
    return corpus_data


def generate_i18_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        corpus = load_dir_data(languages[language])
        data[language] = corpus
    return data


def generate_code_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        get_sources(languages[language]["git_urls"], languages[language]["path"])
        corpus = load_dir_data(languages[language])
        data[language] = corpus
    return data


def get_sources(urls: list[str], path: str) -> None:
    for url in urls:
        clone_path = path + "/" + url.replace("https://", "").replace("/", "___")
        if not os.path.exists(clone_path):
            git.Repo.clone_from(url, clone_path)


def load_dir_data(language: dict) -> dict:
    corpus = {
        "size": 0,
        "count": {
            1: {},
            2: {},
            "transitions": {},
        },
    }
    for _f in sorted(list_files(language["path"], language["extensions"])):
        with open(_f, "r") as file:
            load_file_data(file, corpus)
    return corpus


def list_files(path: str, extensions: list[str]) -> list[str]:
    files = []
    for ext in extensions:
        files += glob.glob(f"{path}/**/*.{ext}", recursive=True)
    return files


def load_file_data(file, corpus: dict) -> None:
    transitions = {}
    for line in file.readlines():
        line = line.strip()
        line = clean_line(line)
        if line:
            load_line(line, transitions, corpus)


def clean_line(line: str) -> str:
    # That map may need to be per language
    translate_map = {
        "\u2014": "--",
        "\u2019": "'",
        "\u201C": '"',
        "\u201D": '"',
    }
    # TODO: This should be a preference
    allowlist = "abcdefghijklmnopqrstuvwxyz"

    _line = list(line.lower())
    for index, char in enumerate(_line):
        if char in translate_map.keys():
            char = translate_map[char]
        if char not in allowlist:
            char = " "
        _line[index] = char
    line = "".join(_line)
    line = line.strip()
    return line


def load_line(line: str, transitions: dict, corpus: dict) -> None:
    last_char = "\n"
    corpus["size"] += 1
    for char in line:
        load_char(char, last_char, transitions, corpus)
        last_char = char
    load_char("\n", char, transitions, corpus)


def load_char(char: str, last_char: str, transitions: dict, corpus: dict) -> None:
    corpus["size"] += 1
    corpus["count"][1][char] = corpus["count"][1].get(char, 0) + 1
    corpus["count"][2][last_char] = corpus["count"][2].get(last_char, {})
    corpus["count"][2][last_char][char] = corpus["count"][2][last_char].get(char, 0) + 1
    for tchar in transitions.keys():
        if tchar == char:
            corpus["count"]["transitions"][char] = corpus["count"]["transitions"].get(
                char, {}
            )
            for tchar in transitions[char]:
                corpus["count"]["transitions"][char][tchar] = (
                    corpus["count"]["transitions"][char].get(tchar, 0) + 1
                )
            transitions[char].clear()
        else:
            transitions[tchar] = transitions.get(tchar, set())
            transitions[tchar].add(char)


def consolidate_data(language_data: dict, language_weight: dict) -> dict:
    corpus_data = {
        "char": set(),
        "language": language_data,
    }

    for language, corpus in language_data.items():
        print()
        print(f"{language}: {language_weight[language]}")
        corpus_data["char"].update(corpus["count"][1].keys())
        corpus["weight"] = language_weight[language]
    return corpus_data
