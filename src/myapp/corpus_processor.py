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
    language_data.update(generate_i18_data(corpus_preferences["i18n"], language_weight))
    language_data.update(
        generate_code_data(corpus_preferences["code"], language_weight)
    )
    corpus_data = consolidate_data(language_data, corpus_preferences)
    if abs(sum(corpus_data["char"].values()) - 1) > 10 ** (-3):
        raise Exception("Error while processing corpus")
    total = 0.0
    for char in corpus_data["bigram"].values():
        total += sum(char.values())
    if abs(total - 1) > 10 ** (-3):
        raise Exception("Error while processing corpus")
    with open("corpus.yaml", "w") as outfile:
        yaml.dump(corpus_data, outfile, sort_keys=True)
    return corpus_data


def generate_i18_data(languages: dict, language_weight: dict) -> dict:
    data = {}
    for language in languages.keys():
        corpus = load_dir_data(languages[language])
        normalize_data(corpus, language_weight[language])
        data[language] = corpus
    return data


def generate_code_data(languages: dict, language_weight: dict) -> dict:
    data = {}
    for language in languages.keys():
        print(language)
        get_sources(languages[language]["git_urls"], languages[language]["path"])
        corpus = load_dir_data(languages[language])
        normalize_data(corpus, language_weight[language])
        data[language] = corpus
    return data


def normalize_data(corpus, weight):
    total = sum(corpus["char"].values())
    for char, value in corpus["char"].items():
        corpus["char"][char] = weight * value / total

    for char, chars2 in corpus["bigram"].items():
        for char2, value in chars2.items():
            corpus["bigram"][char][char2] = weight * value / total


def get_sources(urls: list[str], path: str) -> None:
    for url in urls:
        clone_path = path + "/" + url.replace("https://", "").replace("/", "___")
        if not os.path.exists(clone_path):
            git.Repo.clone_from(url, clone_path)


def load_dir_data(language: dict) -> dict:
    corpus = {
        "char": {},
        "bigram": {},
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


def load_file_data(file, corpus) -> None:
    previous_char = "\\n"
    for line in file.readlines():
        line = line.strip()
        line = clean_line(line)
        previous_char = load_line(line, previous_char, corpus)
        previous_char = add_char("\\n", previous_char, corpus)
    return


def clean_line(line: str) -> str:
    # That map may need to be per language
    translate_map = {
        "\u2014": "-",
        "\u2019": "'",
        "\u201C": '"',
        "\u201D": '"',
    }
    # That map may need to be per language.
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


def load_line(line, previous_char, corpus) -> str:
    first = True
    for word in line.split():
        if first is False:
            previous_char = add_char("\\s", previous_char, corpus)
        previous_char = load_word(word, previous_char, corpus)
        first = False
    return previous_char


def load_word(word, previous_char, corpus) -> str:
    for char in word:
        previous_char = add_char(char, previous_char, corpus)
    return previous_char


def add_char(char, previous_char, corpus):
    corpus["char"][char] = corpus["char"].get(char, 0) + 1
    corpus["bigram"][previous_char] = corpus["bigram"].get(previous_char, {})
    corpus["bigram"][previous_char][char] = (
        corpus["bigram"][previous_char].get(char, 0) + 1
    )
    return char


def consolidate_data(language_data: dict, corpus_preferences: dict) -> dict:
    corpus_data = {
        "char": dict(),
        "bigram": {},
    }

    for language, corpus in language_data.items():
        print()
        print(language)

        for char, value in corpus["char"].items():
            corpus_data["char"][char] = corpus_data["char"].get(char, 0) + value

        for char, chars2 in corpus["bigram"].items():
            corpus_data["bigram"][char] = corpus_data["bigram"].get(char, {})
            for char2, value in chars2.items():
                corpus_data["bigram"][char][char2] = (
                    corpus_data["bigram"][char].get(char2, 0) + value
                )

    return corpus_data
