from bs4 import BeautifulSoup
import cloudscraper


FEN_INDEX = "https://papers.ssrn.com/sol3/Jeljour_results.cfm?form_name=journalBrowse&journal_id=203"

scraper = cloudscraper.create_scraper()
response = scraper.get(FEN_INDEX)

if response.status_code != 200:
    print("Error fetching index page: ", response.status_code)
    exit

soup = BeautifulSoup(response.content, features="html.parser")
hidden_paper_ids_input = soup.find("input", id="listAB_ID")
paper_ids = hidden_paper_ids_input["value"].split(",")


f = open("./data/fen_paper_ids.txt", "w+")
f.write("\n".join(paper_ids))
f.close()

