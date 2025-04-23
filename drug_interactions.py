###drug_interactions.py
#this code takes drug name input from a user, translates from brand to scientific name if necessary, checks the drug for interactions against the FDA database, and then prints out whether the drug has interactions with other drugs, and what they are.
import csv
from operator import itemgetter

#Step 1: load brand --> science mapping
name_map = {}

with open("brand_science_names.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        brand = row["brand_name"].strip().lower()
        science = row["science_name"].strip().lower()

        name_map[science] = science
        name_map[brand] = science

#Step 2: load drug-drug interactions
interactions = []

with open("db_drug_interactions.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        interactions.append({
            "drug1": row["Drug 1"].strip(),
            "drug2": row["Drug 2"].strip(),
            "description": row["Interaction Description"].strip()
        })


#Step 3: get user input
query = input("Enter the name of a drug: ").strip().lower()
normalized_query = name_map.get(query)

if not normalized_query:
    print("Sorry, that drug name wasn't recognized.")
    exit()

#Step 4: search for user input within interaction database and create a list of interactions
found = False
interacting_drugs = []

for entry in interactions:
    drug1 = entry["drug1"]
    drug2 = entry["drug2"]
    description = entry["description"]

    if drug1.lower() == normalized_query:
        interacting_drugs.append((drug2, description))
        found = True
    elif drug2.lower() == normalized_query:
        interacting_drugs.append((drug1, description))
        found = True

if found:
    interacting_drugs.sort(key=itemgetter(0))
    print(f"\n{query.capitalize()} (mapped to {normalized_query.capitalize()}) has interactions with:\n")
    for drug, desc in interacting_drugs:
        print(f"{drug}: {desc}")
else:
    print("No interactions found for that drug.")
