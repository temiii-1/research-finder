import requests
import json
import re

# Query ClinicalTrials.gov API for actively recruiting UT Austin studies
url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.term": "University of Texas Austin",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 200,
}

response = requests.get(url, params=params)
print("Status code:", response.status_code)
print("Response preview:", response.text[:200])
data = response.json()

studies = []

CATEGORY_MAP = {
    "ptsd": "PTSD/Trauma",
    "ptsd, post traumatic stress disorder": "PTSD/Trauma",
    "post-traumatic stress disorder": "PTSD/Trauma",
    "posttraumatic stress disorder (ptsd)": "PTSD/Trauma",
    
    "depression": "Major Depression / Treatment Resistant Depression",
    "depressive disorder, major": "Major Depression / Treatment Resistant Depression",
    "major depressive disorder": "Major Depression / Treatment Resistant Depression",
    "treatment resistant depression": "Major Depression / Treatment Resistant Depression",
    
    "anxiety": "Generalized Anxiety Disorder",
    "generalized anxiety disorder": "Generalized Anxiety Disorder",
    
    "bipolar disorder": "Bipolar Disorder",
    
    "obsessive-compulsive disorder": "Obsessive-Compulsive Disorder",
    
    "panic disorder": "Panic Disorder",
    
    "social anxiety disorder": "Social Anxiety Disorder",
    
    "postpartum depression": "Postpartum Depression",
    
    "pregnancy": "Pregnancy",
    "pregnancy preterm": "Pregnancy",
    
    "healthy adults": "Healthy Adult – 18-70 Years Old",
    
    "crohn disease": "Crohn's Disease",
    "crohn's disease": "Crohn's Disease",
    
    "primary progressive aphasia(ppa)": "Primary Progressive Aphasia",
    "primary progressive aphasia": "Primary Progressive Aphasia",
}

for study in data.get("studies", []):
    protocol = study.get("protocolSection", {})

    raw_date = protocol.get("statusModule", {}).get("studyFirstSubmitDate", "")
    if raw_date:
        parts = raw_date.split("-")
        date = f"{parts[1]}/{parts[2]}/{parts[0]}"
    else:
        date = ""

    # get category from conditions
    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
    raw_category = conditions[0] if conditions else "Other"
    category = CATEGORY_MAP.get(raw_category.lower(), raw_category)
    
    title = protocol.get("identificationModule", {}).get("briefTitle", "")
    description = protocol.get("descriptionModule", {}).get("briefSummary", "")
    # remove escaped (/) characters from description
    description = re.sub(r"\\([~><=#\-\*\.])", r"\1", description)
    raw_eligibility = protocol.get("eligibilityModule", {}).get("eligibilityCriteria", "")

    # split into inclusion and exclusion sections
    eligibility_items = []
    if raw_eligibility:
        lines = raw_eligibility.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("inclusion criteria") or line.lower().startswith("exclusion criteria"):
                eligibility_items.append(f"**{line}**")
            else:
                line = line.replace("* ", "").replace("*", "").strip()
                line = re.sub(r"^\d+\.\s*", "", line)
                line = re.sub(r"^\\?-\s*", "", line)
                line = re.sub(r"\\([~><=#\-\*\.])", r"\1", line)
                if line:
                    # if line ends with colon, treat as subheader
                    if line.endswith(":"):
                        eligibility_items.append(f"**{line}**")
                    else:
                        eligibility_items.append(f"  {line}")

    eligibility = eligibility_items
    
    min_age = protocol.get("eligibilityModule", {}).get("minimumAge", "")
    max_age = protocol.get("eligibilityModule", {}).get("maximumAge", "")
    nct_id = protocol.get("identificationModule", {}).get("nctId", "")

    contacts = protocol.get("contactsLocationsModule", {}).get("centralContacts", [])
    contact = ""
    if contacts:
        contact = f"{contacts[0].get('name', '')} {contacts[0].get('email', '')}"


    if "utexas.edu" not in contact.lower():
        continue

    studies.append({
        "title": title,
        "date": date,
        "description": description,
        "eligibility": eligibility,
        "compensation": "",
        "contact": contact,
        "category": category,
        "source": f"https://clinicaltrials.gov/study/{nct_id}",
        "min_age": min_age,
        "max_age": max_age
    })

print(f"Found {len(studies)} recruiting UT Austin studies")
for study in studies[:5]:
    print(f"TITLE: {study['title'][:60]}")
    print(f"CONTACT: {study['contact']}")
    print(f"DATE: {study['date']}")
    print(f"CATEGORY: {study['category']}")
    print("---")

with open("clinicaltrials.json", "w") as f:
    json.dump(studies, f, indent=2)

print("Saved to clinicaltrials.json")