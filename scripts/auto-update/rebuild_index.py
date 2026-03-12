import json
import os
import glob

from config import load as _load_config

def rebuild_index(dist_dir: str | None = None):
    _cfg = _load_config()
    public_db_dir = dist_dir or _cfg["dist_dir"]
    search_path = os.path.join(public_db_dir, 'search.json')
    update_path = os.path.join(public_db_dir, 'update.json')
    
    from datetime import datetime, timedelta

    # Find all monthly JSON files
    monthly_files = glob.glob(os.path.join(public_db_dir, '[0-9][0-9][0-9][0-9]-[0-9][0-9]*.json'))
    monthly_files.sort()
    
    print(f"Found {len(monthly_files)} monthly data files.")
    
    search_data = []
    all_dates = set()
    month_mapping = {}

    for fpath in monthly_files:
        fname = os.path.basename(fpath)
        month_key = fname[:7] # YYYY-MM
        month_mapping[month_key] = fname

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                entries = json.load(f)
                
                for entry in entries:
                    d = entry.get("date")
                    if d:
                        all_dates.add(d)
                        
                    if not entry.get('no_data') and entry.get('title'):
                        search_data.append({
                            "d": entry.get("date"),
                            "t": entry.get("title"),
                            "e": entry.get("explanation", "")
                        })
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    # 1. Save search index (Sort by date descending)
    search_data.sort(key=lambda x: x['d'], reverse=True)
    with open(search_path, 'w', encoding='utf-8') as f:
        json.dump(search_data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Search index rebuilt: {len(search_data)} entries")

    # 2. Build update.json (Ranges only)
    sorted_dates = sorted(list(all_dates))
    ranges = []
    if sorted_dates:
        start = sorted_dates[0]
        prev = sorted_dates[0]
        for i in range(1, len(sorted_dates)):
            curr = sorted_dates[i]
            prev_dt = datetime.strptime(prev, "%Y-%m-%d")
            curr_dt = datetime.strptime(curr, "%Y-%m-%d")
            if curr_dt - prev_dt > timedelta(days=1):
                ranges.append([start, prev])
                start = curr
            prev = curr
        ranges.append([start, prev])

    update_payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "ranges": ranges,
        "files": month_mapping
    }
    with open(update_path, "w", encoding="utf-8") as f:
        json.dump(update_payload, f, ensure_ascii=False, indent=2)
    print(f"Update index rebuilt: {len(ranges)} ranges, {len(month_mapping)} files")
    print(f"Done. Files saved to {public_db_dir}")

if __name__ == "__main__":
    rebuild_index()
