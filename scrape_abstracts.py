import json
import os.path
import sys
from typing import List, Dict

from tqdm import tqdm
import cloudscraper


def scrape(research_network: str):
    ids = get_ids(research_network, 2272481)

    data = get_existing_data(research_network)
    completed_ids = set([d["id"] for d in data])
    scraper = cloudscraper.create_scraper()

    for id in tqdm(ids):
        if id in completed_ids:
            continue

        url = f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={id}"
        response = scraper.get(url)

        save_abstract_data(research_network, {
            "id": id,
            "url": url,
            "error": response.status_code != 200,
            "status_code": response.status_code,
            "html": remove_blank_space(response.text),
        })


def get_ids(research_network: str, min_id = 0) -> List[str]:
    """Gets ids for specified research network in a descending order"""
    with open(f"./data/{research_network}_ids.txt", "r") as f:
        text = f.read()
        ids = text.split("\n")
        ids = map(lambda id: int(id), ids)
        ids = list(filter(lambda id: id > min_id, ids))
        ids.sort(reverse=True, key=int)
        return ids

def get_existing_data(research_network: str) -> List[Dict[str, str]]:
    file_name = f"./data/{research_network}_raw_abstracts.json"
    if not os.path.isfile(file_name):
        return []

    with open(file_name, "r") as f:
        text = f.read()
        return json.loads(text)

def remove_blank_space(text: str):
    filtered_lines = [line for line in text.split('\r\n') if line.strip() != '']
    return "\n".join(filtered_lines)

def save_abstract_data(research_network: str, data: Dict[str, str]):
    json_data = json.dumps(data, indent=4)
    file_name = f"./data/{research_network}_raw_abstracts.json"

    if os.path.isfile(file_name):
        delete_last_line(file_name)
        json_data = ",\n" + json_data + "\n]"
    else:
        json_data = "[\n" + json_data + "\n]"

    with open(f"./data/{research_network}_raw_abstracts.json", "a+") as f:
        f.write(json_data)

def delete_last_line(file_name: str):
    with open(file_name, "r+", encoding = "utf-8") as file:
        file.seek(0, os.SEEK_END)
        pos = file.tell() - 1

        # Read each character in the file one at a time from the penultimate
        # character going backwards, searching for a newline character
        # If we find a new line, exit the search
        while pos > 0 and file.read(1) != "\n":
            pos -= 1
            file.seek(pos, os.SEEK_SET)

        # So long as we're not at the start of the file, delete all the characters ahead
        # of this position
        if pos > 0:
            file.seek(pos, os.SEEK_SET)
            file.truncate()

if __name__ == "__main__":
    scrape("fen")
