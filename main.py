import pandas as pd
from tqdm import tqdm
from intelligent_scraper import crawl
from RAG import get_dict_from_json
from main_chemical_extraction import property_name, chemical_name

query = lambda property_name, chemical_name: f"{property_name} of {chemical_name}"

instructions = "You are a helpful assistant."

prompt = lambda property_name, chemical_name: f"""Extract {property_name} of {chemical_name} and put them in the json below:
```json
{{
    "{property_name}": {{
        "value": Value of the property. (Should be a float or int),
        "lower_limit": Lower Limit of the property. (Should be a float or int),
        "upper_limit": Upper Limit of the property. (Should be a float or int),
        "unit": Unit of the property.
    }}
}}
```

NOTE: If a value not present in the texts, fill with null."""

property_name = "molar_mass"
chemical_name = "benzene"

print(crawl(query(property_name, chemical_name),
      prompt(property_name, chemical_name),
      instructions
))