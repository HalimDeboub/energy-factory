"""
File 1: explore_api.py
Purpose: Understand the data structure from the API
Why: Before we build anything complex, we need to know what data we have

"""

import requests
import json

# Step 1: Fetch a small sample
url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?limit=3"
response = requests.get(url)

# Step 2: Check if request succeeded
if response.status_code == 200:
    data = response.json()
    
    # Step 3: Print the structure
    print("=== API RESPONSE STRUCTURE ===")
    print(f"Top-level keys: {list(data.keys())}")
    
    # Step 4: Look at the actual data format
    print("\n=== FIRST RECORD ===")
    first_record = data['results'][0] if data.get('results') else {}
    
    # Pretty print with indentation
    print(json.dumps(first_record, indent=2, ensure_ascii=False))
    
    # Step 5: Show all available fields
    print("\n=== ALL FIELDS IN A RECORD ===")
    if first_record:
        for key, value in first_record.items():
            print(f"- {key}: {type(value).__name__} = {value}")
            
    # Step 6: Check data types and sample values
    print("\n=== FIELD TYPES SUMMARY ===")
    field_types = {}
    for key, value in first_record.items():
        field_types[key] = type(value).__name__
    
    for field, type_name in field_types.items():
        print(f"{field}: {type_name}")
        
else:
    print(f"Error: {response.status_code}")
    print(response.text)

# Step 7: Check total available records
print("\n=== CHECKING TOTAL RECORDS ===")
count_url = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?limit=1&select=count(*)"
count_response = requests.get(count_url)
if count_response.status_code == 200:
    count_data = count_response.json()
    print(f"Total records available: {count_data.get('total_count', 'Unknown')}")