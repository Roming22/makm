"""Generate input data from the corpus"""
import glob
import os

import git
import yaml


def generate_data(corpus_preferences: dict) -> dict:
    language_data = {}
    language_data.update(generate_i18_data(corpus_preferences["i18n"]))
    language_data.update(generate_code_data(corpus_preferences["code"]))
    corpus_data = consolidate_data(language_data)
    filter_corpus_data = filter_data(corpus_data)
    with open("corpus.yaml", "w") as outfile:
        yaml.dump(corpus_data, outfile, sort_keys=True)
    return corpus_data


def consolidate_data(language_data: dict) -> dict:
    corpus_data = {
        "letter_count": dict(),
        "bigram_count": {},
        "trigram_count": {},
    }
    for _k, count_type in corpus_data.items():
        for _, data in language_data.items():
            for _datapoint, _v in data[_k].items():
                count_type[_datapoint] = count_type.get(_datapoint, 0) + _v
    return corpus_data


def filter_data(corpus_data: dict) -> None:
    delete = []
    for letter, count in corpus_data["letter_count"].items():
        if count < 500:
            delete.append(letter)
    for letter in delete:
        for _c, _v in corpus_data.items():
            for _k in dict(_v).keys():
                if letter in _k:
                    corpus_data[_c].pop(_k)
    for bigram, count in dict(corpus_data["bigram_count"]).items():
        if count < 50:
            corpus_data["bigram_count"].pop(bigram)
    for trigram, count in dict(corpus_data["trigram_count"]).items():
        if count < 100:
            corpus_data["trigram_count"].pop(trigram)


def list_files(path: str, extensions: list[str]) -> list[str]:
    files = []
    for ext in extensions:
        files += glob.glob(f"{path}/**/*.{ext}", recursive=True)
    return files


def generate_i18_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        print("\n", language)
        data[language] = load_dir_data(languages[language])
    return data


def load_dir_data(language: dict) -> dict:
    size = 0
    data = {
        "letter_count": {},
        "bigram_count": {},
        "trigram_count": {},
    }
    for _f in list_files(language["path"], language["extensions"]):
        with open(_f, "r") as file:
            size += load_file_data(file, data)

    # Weight the data based on user preferences
    print("size: ", size)
    for _i, _v1 in data.items():
        print(_i, ":", len(_v1))
        for _j, _v2 in _v1.items():
            data[_i][_j] = float(_v2) * language["weight"] * 1000000.0 / float(size)
    return data


def load_file_data(file, data) -> int:
    size = 0
    for line in file.readlines():
        line = line.strip()
        for word in line.split():
            load_word_data(word, data)
            size += len(word)
    return size


def load_word_data(word, data):
    p0, p1, p2 = None, None, None
    for char in word:
        p0, p1, p2 = clean_char(char.lower()), p0, p1
        data["letter_count"][p0] = data["letter_count"].get(p0, 0) + 1
        if p1 and p1 != p0:
            bigram = "".join(sorted(p0 + p1))
            data["bigram_count"][bigram] = data["bigram_count"].get(bigram, 0) + 1
        if p2 and len({p0, p1, p2}) == 3:
            trigram = sorted([p0 + p1 + p2, p2 + p1 + p0])[0]
            data["trigram_count"][trigram] = data["trigram_count"].get(trigram, 0) + 1


def clean_char(char: str) -> str:
    map = {
        "\u2014": "-",
        "\u2019": "'",
        "\u201C": '"',
        "\u201D": '"',
    }
    return map.get(char, char)


def generate_code_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        print()
        print(language)
        get_sources(languages[language]["git_urls"], languages[language]["path"])
        data[language] = load_dir_data(languages[language])
    return data


def get_sources(urls: list[str], path: str) -> None:
    for url in urls:
        clone_path = path + "/" + url.replace("https://", "").replace("/", "___")
        if not os.path.exists(clone_path):
            git.Repo.clone_from(url, clone_path)
