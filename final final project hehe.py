import csv
import requests
from bs4 import BeautifulSoup
from operator import itemgetter
from openai import OpenAI

#initialize chat gpt
client = OpenAI(api_key="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")

#load brand-science name mapping
name_map = {}
with open("brand_science_names.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        brand = row["brand_name"].strip().lower()
        science = row["science_name"].strip().lower()
        name_map[science] = science
        name_map[brand] = science

#load drug-drug interaction data
interactions = []
with open("db_drug_interactions.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        interactions.append({
            "drug1": row["Drug 1"].strip(),
            "drug2": row["Drug 2"].strip(),
            "description": row["Interaction Description"].strip()
        })

#get user input
query = input("Enter the name of a drug: ").strip().lower()
normalized_query = name_map.get(query)

if not normalized_query:
    print("Sorry, that drug name wasn't recognized.")
    exit()

#search local csv for interactions
interacting_drugs = []
for entry in interactions:
    drug1 = entry["drug1"].lower()
    drug2 = entry["drug2"].lower()
    description = entry["description"]

    if drug1 == normalized_query:
        interacting_drugs.append((drug2, description))
    elif drug2 == normalized_query:
        interacting_drugs.append((drug1, description))

#sort and print
if interacting_drugs:
    interacting_drugs.sort(key=itemgetter(0))
    print(f"\n{query.capitalize()} (mapped to {normalized_query.capitalize()}) has interactions with:\n")
    for drug, desc in interacting_drugs:
        print(f"{drug.capitalize()}: {desc}")
else:
    print("\nNo interactions found for that drug in the local database.")

#wikipedia grabbing
def get_page_title(search_term):
    response = requests.get("https://en.wikipedia.org/w/api.php", params={
        'action': 'query',
        'list': 'search',
        'srsearch': search_term,
        'srlimit': 1,
        'format': 'json'
    })
    data = response.json()
    return data['query']['search'][0]['title'] if data['query']['search'] else None

def get_interactions_section_index(title):
    response = requests.get("https://en.wikipedia.org/w/api.php", params={
        'action': 'parse',
        'page': title,
        'prop': 'sections',
        'format': 'json'
    })
    data = response.json()
    for section in data['parse']['sections']:
        if 'interaction' in section['line'].lower():
            return section['index']
    return None

def get_section_text(title, index):
    response = requests.get("https://en.wikipedia.org/w/api.php", params={
        'action': 'parse',
        'page': title,
        'section': index,
        'prop': 'text',
        'format': 'json'
    })
    data = response.json()
    html_content = data['parse']['text']['*']
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

#wikipedia summary
print("\nSearching Wikipedia...")
wiki_title = get_page_title(normalized_query)
wiki_section_text = ""

if wiki_title:
    index = get_interactions_section_index(wiki_title)
    if index:
        wiki_section_text = get_section_text(wiki_title, index)

#send wikipedia to ai
if wiki_section_text.strip():
    prompt = (
        f"Here is a section from a Wikipedia article about drug interactions:\n\n"
        f"{wiki_section_text.strip()}\n\n"
        f"Please summarize the key interaction-related information in one clear paragraph."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    print("\nWikipedia summary by AI:\n")
    print(response.choices[0].message.content)
else:
    print("\nNo 'Interactions' section found on Wikipedia.")

