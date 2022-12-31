"""Read all the configuration and return a single object with all the data"""

import os.path

import yaml


def read(keyboard: str) -> dict:
    """Read the configuration files"""
    config_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))+"/data/config")
    config = {
        "keyboard": load_yaml(f"{config_dir}/keyboards/{keyboard}.yaml"),
    }
    return config

def load_yaml(filepath: str) -> dict:
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)