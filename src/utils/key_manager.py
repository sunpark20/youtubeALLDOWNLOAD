import json
import os
from pathlib import Path

# ~/.youtube_downloader_config.json 파일에 키를 저장
CONFIG_FILE = Path.home() / ".youtube_downloader_config.json"

def save_api_key_to_file(api_key: str):
    try:
        config = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        
        config['api_key'] = api_key
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"Failed to save API key: {e}")
        return False

def load_api_key_from_file() -> str:
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('api_key', '')
    except Exception as e:
        print(f"Failed to load API key: {e}")
    return ""

def delete_api_key_from_file():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            if 'api_key' in config:
                del config['api_key']
                
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
    except Exception as e:
        print(f"Failed to delete API key: {e}")
