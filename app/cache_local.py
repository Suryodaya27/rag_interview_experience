import os
import json

def get_cache_path(company_name):
    folder = f"data/{company_name.lower().replace(' ', '_')}"
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "links.json")

def save_links_to_cache(company_name, links):
    path = get_cache_path(company_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2)

def load_links_from_cache(company_name):
    path = get_cache_path(company_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_scraped_data_to_cache(title, data):
    folder = f"data/{title.lower().replace(' ', '_')}"
    path = os.path.join(folder, "scraped_data.json")
    os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return None

def get_scraped_data_path(title):
    folder = f"data/{title.lower().replace(' ', '_')}"
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"scraped_data.json")

def load_scraped_data_from_cache(title):
    path = get_scraped_data_path(title)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None