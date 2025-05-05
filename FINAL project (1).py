
import csv
import requests
from bs4 import BeautifulSoup
from operator import itemgetter
from openai import OpenAI


#stores sets of fruits and vegetables. Also includes two medications dictionaries storing brand and scientific names (organized opposite)
fruits = {
   "apple", "banana", "orange", "mango", "pineapple", "strawberry", "blueberry", "raspberry", "blackberry", "cherry",
   "grape", "kiwi", "watermelon", "cantaloupe", "honeydew", "papaya", "passionfruit", "dragon fruit", "lychee", "longan",
   "durian", "jackfruit", "fig", "date", "pomegranate", "guava", "apricot", "peach", "plum", "nectarine", "persimmon",
   "cranberry", "gooseberry", "mulberry", "boysenberry", "elderberry", "starfruit", "rambutan", "sapodilla", "loquat",
   "tamarind", "mangosteen", "soursop", "sugar apple", "custard apple", "cherimoya", "ackee", "ugli fruit", "jujube",
   "kumquat", "clementine", "tangerine", "blood orange", "navel orange", "lemon", "lime", "key lime", "calamansi",
   "buddha’s hand", "yuzu", "salak", "miracle fruit", "medlar", "quince", "cloudberry", "huckleberry", "acerola",
   "maracuja", "camu camu", "bael fruit", "indian gooseberry", "nance", "cempedak", "jabuticaba", "feijoa", "chokecherry",
   "sea buckthorn", "sorb apple", "lúcuma", "mamoncillo", "buddha coconut", "ice cream bean", "santol", "rose apple",
   "ambarella", "bilberry", "white currant", "red currant", "black currant", "desert lime", "wild lime", "finger lime",
   "breadfruit", "oil palm fruit", "olive", "tomato", "cucumber", "zucchini", "avocado", "plantain", "grapefruit"
}


vegetables = {
   "artichoke", "arugula", "asparagus", "avocado", "bamboo shoot", "bean sprout", "beet", "belgian endive", "bell pepper",
   "bitter melon", "bok choy", "broccoli", "broccolini", "brussels sprout", "butternut squash", "cabbage", "carrot",
   "cauliflower", "celeriac", "celery", "chard", "chickpea", "chinese broccoli", "chive", "collard green", "corn",
   "courgette", "cucumber", "daikon", "dandelion green", "edamame", "eggplant", "endive", "fennel", "fiddlehead",
   "galangal", "garlic", "ginger", "green bean", "green onion", "horseradish", "jicama", "kale", "kohlrabi", "leek",
   "lentil", "lettuce", "lima bean", "mung bean", "mustard green", "napa cabbage", "nettle", "okra", "onion", "parsnip",
   "pea", "pea shoot", "pepper", "potato", "pumpkin", "radicchio", "radish", "rapini", "red cabbage", "rhubarb",
   "rutabaga", "scallion", "shallot", "snow pea", "sorrel", "soybean", "spinach", "squash", "sweet potato", "swiss chard",
   "taro", "tomatillo", "tomato", "turnip", "water chestnut", "watercress", "wax bean", "white radish", "yam",
   "yellow squash", "zucchini", "celery root", "cassava", "choko", "purslane", "malabar spinach", "mizuna", "tatsoi",
   "seaweed", "lotus root", "amaranth leaves", "moringa", "hearts of palm", "pak choi"
}


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
import re


fruit_interactions = set()
vegetable_interactions = set()


#fruits = {"banana", "pineapple"} # these are examples!!!
#vegetables = {"broccoli", "spinach"}


def remove_punctuation(text):
   return re.sub(r'[^\w\s]', '', text)


# Example usage
# text = "broccoli and spinach can make your tummy hurt!"
wiki_output = remove_punctuation(wiki_section_text)
wiki_output = wiki_output.lower()
#print(wiki_output)


wiki_output = wiki_output.split(" ")


for word in wiki_output:
   if word in fruits:
       fruit_interactions.add(word)
   if word in vegetables:
       vegetable_interactions.add(word)


if len(fruit_interactions) > 0 or len(vegetable_interactions) > 0:
   print("It looks like there are some fruit or vegetable interactions that you should be careful of:")
   if vegetable_interactions:
      vegetable_interactions = ",".join(vegetable_interactions)
      print(vegetable_interactions.capitalize())

   if fruit_interactions:
      fruit_interactions = ",".join(fruit_interactions)
      print(fruit_interactions.capitalize())

else:
   print("Nice! Doesn't look like there are any fruit or vegetable interactions!")


#send wikipedia to ai
if wiki_section_text.strip():
   prompt = (
       f"Here is a section from a Wikipedia article about drug interactions:\n\n"
       f"{wiki_section_text.strip()}\n\n"
       f"Please summarize the key drug specific interaction-related information in one clear paragraph."
       f"Now please summarize the key fruit interactions which are {fruit_interactions} and and the key vegetable interactions which are {vegetable_interactions} with the drug {normalized_query} in one succinct paragraph"
   )


   response = client.chat.completions.create(
       model="gpt-3.5-turbo",
       messages=[{"role": "user", "content": prompt}]
   )


   print("\nWikipedia summary by AI:\n")
   print(response.choices[0].message.content)
else:
   print("\nNo 'Interactions' section found on Wikipedia.")
