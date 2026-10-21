# duplicate-finder

Find **duplicate files by content hash** (SHA-256). Point it at a folder and it tells you which files are byte-identical and how much space the extras waste — without deleting anything on its own.

**Why hash, not filename:** the same photo downloaded twice with different names is a duplicate; two files with the same name but different content are not. Only content comparison gets this right.

## What it does

- Scans a directory **recursively**
- Uses a fast **size pre-filter**, so only files sharing the same size get hashed (quick on big folders)
- Reports each duplicate group: SHA-256, file size, and all copies
- Optional: export the results as **JSON**, or **quarantine** extra copies into a review folder (`--move`) — originals are never deleted

## How to run

Needs **Python 3.8+**. No dependencies — standard library only.

```bash
python3 duplicate_finder.py /path/to/folder
python3 duplicate_finder.py /path/to/folder --min-size 1048576
python3 duplicate_finder.py /path/to/folder --json duplicates.json
python3 duplicate_finder.py /path/to/folder --move ~/dupes-to-review
python3 duplicate_finder.py /path/to/folder --extensions jpg,png,mp4
```

| Flag | What it does |
|---|---|
| `--min-size BYTES` | Skip files smaller than this (default `1`) |
| `--json PATH` | Write duplicate groups to a JSON file |
| `--move DIR` | Copy extra copies (keeping the first of each group) into `DIR` for manual review. Nothing is deleted. |
| `--extensions exts` | Only scan these extensions, e.g. `jpg,png,mp4` |

## Example output

```
Scanned 14 candidate files (120 total).
Found 2 duplicate group(s), 2.1 MB reclaimable:

[1] 1.1 MB each, 3 copies:
    /photos/IMG_2041.jpg
    /photos/downloads/IMG_2041.jpg
    /photos/backup/IMG_2041 (1).jpg

[2] 512.0 KB each, 2 copies:
    /docs/report-final.pdf
    /docs/report-final-copy.pdf
```

## Safety notes

- The tool is **read-only by default**: it only reads files to hash them.
- `--move` copies the extra copies elsewhere; it never deletes or moves originals. Deleting is your call, after you review.
- Files you can't read (permissions) are skipped, not crashed on.

---

*Small tools that turn repeated annoyances into one-liners — part of a daily utility series.*
