---
description: How to rebuild the search index from monthly data
---

This workflow regenerates the `public/database/search.json` file by aggregating all monthly JSON files in `public/database/`. Use this if the search results are incomplete or if raw data is missing.

### Steps

1. **Ensure Python is installed**
   The script requires a standard Python 3.x environment.

2. **Run the rebuild script**
   Execute the following command from the project root:

   ```bash
   python scripts/rebuild_index.py
   ```

3. **Verify the output**
   Check that `public/database/search.json` has been updated and its size is reasonable (usually several megabytes).

// turbo 4. **Commit changes (optional)**
If running locally and you want to persist the index:

```bash
git add public/database/search.json
git commit -m "chore: rebuild search index"
```
