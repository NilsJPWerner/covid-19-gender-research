import json
import ijson
import csv
import os
import re
from typing import List, Dict, Generator
from bs4 import BeautifulSoup
from tqdm import tqdm


def process_abstracts(research_network: str, csv_output: bool):
    raw_abstracts = get_raw_abstracts(research_network)

    progress = tqdm(raw_abstracts, total=get_raw_abstracts_len(research_network))
    parsed_abstracts = []
    invalid_abstracts = []

    for raw_abstract in progress:
        progress.set_description(f"ID: {raw_abstract['id']}. Invalid abstracts: {len(invalid_abstracts)}")

        if invalid_abstract(raw_abstract):
            invalid_abstracts.append(raw_abstract["id"])
            continue

        try:
            parsed_abstracts.append(process_abstract(raw_abstract))
        except Exception as e:
            print(raw_abstract["url"])
            print(e.with_traceback())
            exit(0)

        if len(parsed_abstracts) > 1000:
            break

    print(f"Invalid abstract ids: {invalid_abstracts}")
    if csv_output:
        output_csv_abstracts(research_network, parsed_abstracts)
    else:
        output_json_abstracts(research_network, parsed_abstracts)

def process_abstract(raw_abstract: Dict[str, str]):
    soup = BeautifulSoup(raw_abstract["html"], features="html.parser")
    abstract_box = soup.find("div", class_="box-abstract-main")

    return {
        "id": raw_abstract["id"],
        "url": raw_abstract["url"],
        "title": abstract_box.find("h1").text,
        "reference": get_reference(soup),
        "date_posted": get_date_posted(soup),
        "last_revised": get_last_revised(soup),
        "date_written": get_date_written(soup),
        "authors": get_authors(soup),
    }

def get_reference(soup: BeautifulSoup):
    reference_div = soup.find("div", class_="reference-info")
    reference_link = reference_div.find("a")
    if reference_link == None:
        return None
    return reference_link.text

def get_date_posted(soup: BeautifulSoup):
    abstract_box = soup.find("div", class_="box-abstract-main")
    raw_text = abstract_box.text
    match = re.search(r"Posted:\s*(\d+\s*\w+\s*\d+)", raw_text)
    if match == None:
        raise Exception("No Posted date found")
    return match.groups()[0]

def get_last_revised(soup: BeautifulSoup):
    abstract_box = soup.find("div", class_="box-abstract-main")
    raw_text = abstract_box.text
    match = re.search(r"Last revised:\s*(\d+\s*\w+\s*\d+)", raw_text)
    if match == None:
        return None
    return match.groups()[0]

def get_date_written(soup: BeautifulSoup):
    abstract_box = soup.find("div", class_="box-abstract-main")
    raw_text = abstract_box.text
    match = re.search(r"Date Written:\s([\d\w\ ]*)", raw_text)
    if match == None:
        return None
    return match.groups()[0]

def get_authors(soup: BeautifulSoup):
    authors_section = soup.find("div", class_="authors")
    raw_authors = authors_section.find_all("h2")
    raw_universities = authors_section.find_all("p")

    authors = []

    for i, raw_author in enumerate(raw_authors):
        author_link = raw_author.find("a")

        university = raw_author.find_next("p")
        university_link = university.find("a")

        if university_link is not None:
            university_name = university_link.text
            university_url = university_link["href"]
        else:
            university_name = university.text
            university_url = None

        authors.append({
            "url": author_link["href"],
            "position": i + 1,
            "name": author_link.text,
            "university_name": university_name,
            "university_url": university_url,
        })

    return authors

def invalid_abstract(raw_abstract) -> bool:
    return "The abstract you requested was not found" in raw_abstract["html"]

def get_raw_abstracts(research_network: str) -> Generator[Dict[str, str], None, None]:
    file_name = f"./data/{research_network}_raw_abstracts.json"
    if not os.path.isfile(file_name):
        raise Exception("File not found")

    with open(file_name, "r") as f:
        items = ijson.items(f, "item")
        objects = (o for o in items)
        for o in objects:
            yield o

def get_raw_abstracts_len(research_network: str) -> int:
    return sum(1 for _ in get_raw_abstracts(research_network))

def output_json_abstracts(research_network:str, abstracts: List[Dict[str, str]]):
    file_name = f"./data/{research_network}_parsed_abstracts.json"
    data = json.dumps(abstracts, indent=4, ensure_ascii=False)
    with open(file_name, "w+") as f:
        f.write(data)

def output_csv_abstracts(research_network:str, abstracts: List[Dict[str, str]]):
    file_name = f"./data/{research_network}_parsed_abstracts.csv"
    with open(file_name, "w+") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "author_name", "author_url", "author_position", "university_name", "university_url", "paper_id", "paper_title", "paper_url", "paper_reference", "date_posted",
            "last_revised", "date_written"
        ])

        for paper in abstracts:
            for author in paper["authors"]:
                csv_writer.writerow([
                    author["name"], author["url"], author["position"], author["university_name"],
                    author["university_url"], paper["id"], paper["title"], paper["url"],
                    paper["reference"], paper["date_posted"], paper["last_revised"], paper["date_written"],
                ])

if __name__ == "__main__":
    process_abstracts("fen", True)
    # process_abstracts("test")
