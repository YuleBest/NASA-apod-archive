import json
import os

search_path = 'public/database/search.json'

if os.path.exists(search_path):
    with open(search_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        count_2024 = sum(1 for entry in data if entry['d'].startswith('2024'))
        print(f"Total entries for 2024: {count_2024}")
        if count_2024 > 0:
            print("Sample 2024 entry:")
            for entry in data:
                if entry['d'].startswith('2024'):
                    print(json.dumps(entry, indent=2))
                    break
        
        # Also check for CG 4 again with regex-like check
        print("\nChecking for 'CG 4' (case insensitive, flexible spacing):")
        import re
        pattern = re.compile(r'CG\s*4', re.IGNORECASE)
        for entry in data:
            if pattern.search(entry['t']):
                print(f"Match found: {entry['t']} ({entry['d']})")
else:
    print(f"{search_path} not found")
