import requests
from bs4 import BeautifulSoup

url = "https://www.healthyhorns.utexas.edu/patient-research-opportunities.html"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

studies = []
current_category = "Uncategorized"

COMPENSATION_KEYWORDS = ["receive", "get", "compensat", "what you will"]
EXCLUSION_KEYWORDS = ["exclusion", "not eligible", "must not"]
INCLUSION_KEYWORDS = ["inclusion", "must be", "eligibility", "qualified"]
CONTACT_KEYWORDS = ["contact", "interested", "principal investigator"]

for element in soup.find_all(["button", "h3"]):

    if element.name == "button" and "accordion-button" in element.get("class", []):
        current_category = element.text.strip()

    elif element.name == "h3":   
        study = {
            "title": element.text.strip(),
            "category": current_category, 
            "date": "",
            "description": "",
            "eligibility": [],
            "compensation": "",
            "contact": ""
        }

        next_element = element.find_next_sibling()
        current_section = "description"

        while next_element and next_element.name != "h3":
            text = next_element.text.strip()
            text_lower = text.lower()

            if next_element.name == "p":
                # Check if it's a date (starts with numbers like 6/18/2025)
                if not study["date"] and len(text) < 15 and any(c.isdigit() for c in text):
                    study["date"] = text

                # Check strong tags inside p to determine next section
                strong = next_element.find("strong")
                if strong:
                    strong_text = strong.text.lower()
                    if any(k in strong_text for k in COMPENSATION_KEYWORDS):
                        current_section = "compensation"
                    elif any(k in strong_text for k in EXCLUSION_KEYWORDS):
                        current_section = "exclusion"
                    elif any(k in strong_text for k in INCLUSION_KEYWORDS):
                        current_section = "eligibility"
                    elif any(k in strong_text for k in CONTACT_KEYWORDS):
                        current_section = "contact"
                    else:
                        current_section = "description"
                else:
                    if any(k in text_lower for k in CONTACT_KEYWORDS):
                        current_section = "contact"

                # Add text to the right section
                if current_section == "contact":
                    study["contact"] += text + " "
                elif current_section == "description":
                    if text and not study["date"] == text:
                        study["description"] += text + " "

            elif next_element.name == "ul":
                items = [li.text.strip() for li in next_element.find_all("li")]
                if current_section == "compensation":
                    study["compensation"] = " ".join(items)
                elif current_section in ["eligibility", "exclusion"]:
                    study["eligibility"].extend(items)
                elif current_section == "contact":
                    study["contact"] += " ".join(items) + " "

            elif next_element.name == "strong":
                text_lower = next_element.text.lower()
                if any(k in text_lower for k in COMPENSATION_KEYWORDS):
                    current_section = "compensation"
                elif any(k in text_lower for k in EXCLUSION_KEYWORDS):
                    current_section = "exclusion"
                elif any(k in text_lower for k in INCLUSION_KEYWORDS):
                    current_section = "eligibility"
                elif any(k in text_lower for k in CONTACT_KEYWORDS):
                    current_section = "contact"

            next_element = next_element.find_next_sibling()

        studies.append(study)

seen_titles = set()
unique_studies = []
for study in studies:
    if study["title"] not in seen_titles:
        seen_titles.add(study["title"])
        unique_studies.append(study)

print(f"Total studies found: {len(unique_studies)}")
print("---")

for study in unique_studies:
    print("CATEGORY:", study["category"])
    print("TITLE:", study["title"])
    print("DATE:", study["date"])
    print("DESCRIPTION:", study["description"][:150])
    print("ELIGIBILITY:", study["eligibility"][:2])
    print("COMPENSATION:", study["compensation"])
    print("CONTACT:", study["contact"][:100])
    print("---")


import json

with open("studies.json", "w") as f:
    json.dump(unique_studies, f, indent=2)

print("Saved to studies.json")