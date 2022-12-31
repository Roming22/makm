"""Generate input data from the corpus"""
import glob
import os

import git


def generate_data(corpus_preferences: dict) -> dict:
    corpus_data = {
        "letter_count": {},
        "bigram_count": {},
        "trigram_count": {},
    }
    language_data = {}
    language_data.update(generate_i18_data(corpus_preferences["i18n"]))
    language_data.update(generate_code_data(corpus_preferences["code"]))
    return corpus_data

def list_files(path: str, extensions: list[str]) -> list[str]:
    files = []
    for ext in extensions:
        files += glob.glob(f"{path}/**/*.{ext}", recursive=True)
    return files

def generate_i18_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        data[language] = load_dir_data(languages[language]["path"], ["txt"])
        data[language]["weight"] = languages[language]["weight"]
    return data

def load_dir_data(data_dir: str, extensions: list[str]) -> dict:
    data = {
        "letter_count": {},
        "bigram_count": {},
        "size": 0,
        "trigram_count": {},
    }
    for _f in list_files(data_dir, extensions):
        with open(_f, 'r') as file:
            load_file_data(file, data)
    return data

def load_file_data(file, data) -> None:
    for line in file.readlines():
        line = line.strip()
        for word in line.split():
            load_word_data(word, data)

def load_word_data(word, data):
    p0, p1, p2 = None, None, None
    for char in word:
        p0, p1, p2 = char.lower(), p0, p1
        data["letter_count"][p0] = data["letter_count"].get(p0, 0) + 1
        if p1:
            bigram = "".join(sorted(p0+p1))
            data["bigram_count"][bigram] = data["bigram_count"].get(bigram, 0) + 1
        if p2:
            trigram = sorted([p0+p1+p2, p2+p1+p0])[0]
            data["trigram_count"][trigram] = data["trigram_count"].get(trigram, 0) + 1
        data["size"] += 1

def generate_code_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        get_sources(languages[language]["git_urls"], languages[language]["path"])
        data[language] = load_dir_data(languages[language]["path"], languages[language]["extensions"])
        data[language]["weight"] = languages[language]["weight"]
        print(data[language])
    return data

def get_sources(urls: list[str], path: str) -> None:
    for url in urls:
        clone_path = path + "/" + url.replace("https://", "").replace("/","___")
        print(url, clone_path)
        if not os.path.exists(clone_path):
            git.Repo.clone_from(url, clone_path)