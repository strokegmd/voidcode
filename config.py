import json

global_config = None
global_prompt = None

def get_config() -> dict:
    with open('config.json', 'r') as file:
        config = json.loads(file.read())

    return config

def get_prompt() -> str:
    global global_prompt

    if not global_prompt:
        with open('prompt.txt', 'r') as file:
            global_prompt = file.read()

    return global_prompt

def get_key(key: str) -> any:
    global global_config

    if not global_config:
        global_config = get_config()
    
    return global_config.get(key)
