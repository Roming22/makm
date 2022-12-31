"""Read all the configuration and return a single object with all the data"""

import os.path

import yaml


def read(keyboard: str) -> dict:
    """Read the configuration files"""
    data_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))+"/data")
    config_dir = f"{data_dir}/config"
    config = {
        "keyboard": load_yaml(f"{config_dir}/keyboards/{keyboard}.yaml"),
        "preferences": load_yaml(f"{config_dir}/preferences.yaml"),
    }
    add_path_to_corpus(config["preferences"]["corpus"], data_dir)
    return config

def load_yaml(filepath: str) -> dict:
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

def add_path_to_corpus(config: dict, data_dir:str) -> None:
    for _i in config.keys():
        for _j in config[_i].keys():
            config[_i][_j]["path"] = f"{data_dir}/corpus/{_i}/{_j}"
