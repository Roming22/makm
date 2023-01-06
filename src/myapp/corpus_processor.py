"""Generate input data from the corpus"""
import glob
import os

import git
import yaml


def generate_data(corpus_preferences: dict) -> dict:
    language_data = {}
    language_data.update(generate_i18_data(corpus_preferences["i18n"]))
    language_data.update(generate_code_data(corpus_preferences["code"]))
    corpus_data = consolidate_data(language_data, corpus_preferences)
    filter_data(corpus_data)
    with open("corpus.yaml", "w") as outfile:
        yaml.dump(corpus_data, outfile, sort_keys=True)
    return corpus_data


def consolidate_data(language_data: dict, corpus_preferences: dict) -> dict:
    corpus_data = {
        "letter_count": dict(),
        "bigram_count": {},
        "trigram_count": {},
    }

    weight = {}
    for languages in corpus_preferences.values():
        for language, data in languages.items():
            weight[language] = data["weight"]
    total_weight = sum(weight.values())
    weight = {k: v / total_weight for k, v in weight.items()}

    for language, corpus in language_data.items():
        print()
        print(language)
        for count_type, data in corpus.items():
            print(count_type, ":", len(data.keys()))
            for datapoint, value in data.items():
                corpus_data[count_type][datapoint] = (
                    corpus_data[count_type].get(datapoint, 0)
                    + 100 * value * weight[language]
                )

    return corpus_data


def filter_data(corpus_data: dict) -> None:
    treshold = 1 / 1000
    delete = []
    print()
    print("Corpus")

    before = len(corpus_data["letter_count"].values())
    for item, count in corpus_data["letter_count"].items():
        if count < treshold:
            delete.append(item)
            print(count)
    while delete:
        item = delete.pop()
        for _c, _v in corpus_data.items():
            for _k in dict(_v).keys():
                if item in _k:
                    corpus_data[_c].pop(_k)
    print(f"letter_count: {len(corpus_data['letter_count'].values())} out of {before}")

    before = len(corpus_data["bigram_count"].values())
    for item, count in dict(corpus_data["bigram_count"]).items():
        if count < treshold * treshold:
            delete.append(item)
    while delete:
        item = delete.pop()
        corpus_data["bigram_count"].pop(item)
    print(f"bigram_count: {len(corpus_data['bigram_count'].values())} out of {before}")

    before = len(corpus_data["trigram_count"].values())
    for item, count in dict(corpus_data["trigram_count"]).items():
        if count < treshold * treshold * treshold:
            delete.append(item)
    while delete:
        item = delete.pop()
        corpus_data["trigram_count"].remove(item)
    print(
        f"trigram_count: {len(corpus_data['trigram_count'].values())} out of {before}"
    )


def list_files(path: str, extensions: list[str]) -> list[str]:
    files = []
    for ext in extensions:
        files += glob.glob(f"{path}/**/*.{ext}", recursive=True)
    return files


def generate_i18_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        data[language] = load_dir_data(languages[language])
    return data


def load_dir_data(language: dict) -> dict:
    corpus = {
        "letter_count": {},
        "bigram_count": {},
        "trigram_count": {},
    }
    for _f in list_files(language["path"], language["extensions"]):
        with open(_f, "r") as file:
            load_file_data(file, corpus)

    # Switch values to frequency
    for data in corpus.values():
        total = sum(data.values())
        for input, count in data.items():
            data[input] = count / total
    return corpus


def load_file_data(file, data) -> None:
    for line in file.readlines():
        line = line.strip()
        line = clean_line(line)
        for word in line.split():
            load_word_data(word, data)
            data["letter_count"]["\\s"] = data["letter_count"].get("\\s", 0) + 1
        data["letter_count"]["\\n"] = data["letter_count"].get("\\n", 0) + 1
    return


def load_word_data(word, data) -> None:
    p0, p1, p2 = None, None, None
    for char in word:
        p0, p1, p2 = char, p0, p1
        data["letter_count"][p0] = data["letter_count"].get(p0, 0) + 1
        if p1 and p1 != p0:
            bigram = "".join(sorted(p0 + p1))
            data["bigram_count"][bigram] = data["bigram_count"].get(bigram, 0) + 1
        if p2 and len({p0, p1, p2}) == 3:
            trigram = sorted([p0 + p1 + p2, p2 + p1 + p0])[0]
            data["trigram_count"][trigram] = data["trigram_count"].get(trigram, 0) + 1


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

    _line = list(line)
    for _i, _c in enumerate(_line):
        tr = None
        if _c not in allowlist:
            tr = " "
        elif _c in translate_map.keys():
            tr = translate_map[_c]
        else:
            tr = _c.lower()
        _line[_i] = tr
    line = "".join(_line)
    line = line.strip()
    return line


def generate_code_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        get_sources(languages[language]["git_urls"], languages[language]["path"])
        data[language] = load_dir_data(languages[language])
    return data


def get_sources(urls: list[str], path: str) -> None:
    for url in urls:
        clone_path = path + "/" + url.replace("https://", "").replace("/", "___")
        if not os.path.exists(clone_path):
            git.Repo.clone_from(url, clone_path)
