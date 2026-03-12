import json
import os
import glob

def rebuild_index():
    public_db_dir = 'public/database'
    search_path = os.path.join(public_db_dir, 'search.json')
    
    # Find all monthly JSON files
    monthly_files = glob.glob(os.path.join(public_db_dir, '[0-9][0-9][0-9][0-9]-[0-9][0-9].json'))
    monthly_files.sort()
    
    print(f"Found {len(monthly_files)} monthly data files.")
    
    search_data = []
    
    for fpath in monthly_files:
        month_name = os.path.basename(fpath).replace('.json', '')
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                entries = json.load(f)
                
                added_count = 0
                for entry in entries:
                    if not entry.get('no_data') and entry.get('title'):
                        search_data.append({
                            "d": entry.get("date"),
                            "t": entry.get("title"),
                            "e": entry.get("explanation", "")
                        })
                        added_count += 1
                # print(f"  {month_name}: added {added_count} entries")
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    # Sort search data by date (descending)
    search_data.sort(key=lambda x: x['d'], reverse=True)
    
    print(f"Total searchable entries: {len(search_data)}")
    
    # Save search index
    with open(search_path, 'w', encoding='utf-8') as f:
        # Use compact format
        json.dump(search_data, f, ensure_ascii=False, separators=(",", ":"))
        
    print(f"Search index rebuilt successfully at {search_path}")

if __name__ == "__main__":
    rebuild_index()
