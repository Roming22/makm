"""Generate input data from the corpus"""
import glob


def generate_data(corpus_preferences: dict) -> dict:
    corpus_data = {
        "letter_count": {},
        "bigram_count": {},
        "trigram_count": {},
    }
    language_data = {}
    language_data.update(generate_i18_data(corpus_preferences["i18n"]))
    language_data.update(generate_code_data(corpus_preferences["code"]))
    print(language_data)
    return corpus_data

def list_files(path: str, extensions: list[str]) -> list[str]:
    files = []
    for ext in extensions:
        files += glob.glob(f"{path}/**/*.{ext}", recursive=True)
    return files

def generate_i18_data(languages: dict) -> dict:
    data = {}
    for language in languages.keys():
        data[language] = generate_language_data(languages[language]["path"])
    return data

def generate_language_data(data_dir: str) -> dict:
    data = {
        "letter_count": {},
        "bigram_count": {},
        "size": 0,
        "trigram_count": {},
    }
    for _f in list_files(data_dir, ["txt"]):
        with open(_f, 'r') as file:
            load_language_data(file, data)
    return data

def load_language_data(file, data) -> None:
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
    return data