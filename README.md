# duplicate-finder

Find duplicate files by content — not by name. Walk a folder, group files with
identical SHA-256 hashes, and report each duplicate set with the space it wastes.
Report-only: it never deletes or moves anything.

## Why

Same photo saved in three folders, video exports piling up, "final_v2_FINAL.mp4"
everywhere. Name-based dedup tools miss renames; this one hashes the actual bytes.

## Requirements

- Python 3.8+ (standard library only — no installs)

## How to run

```bash
# scan a folder
python3 dupfind.py ~/Downloads

# ignore tiny files, only video extensions
python3 dupfind.py ~/Videos --min-size 5MB --ext .mp4,.mov,.mkv

# show only the 10 biggest duplicate groups
python3 dupfind.py ~/Pictures --top 10
```

## Example output

```
[1] 3 copies x 248.6 MB = 497.2 MB wasted (sha256:9f2c41aa8b1e...)
      /home/user/Videos/export_final.mp4
      /home/user/Videos/export_final_v2.mp4
      /home/user/Backups/export_final.mp4
[2] 2 copies x 12.4 MB = 12.4 MB wasted (sha256:77bd02f1c9aa...)
      /home/user/Pictures/beach.png
      /home/user/Pictures/old/beach_copy.png

2 duplicate groups, ~509.6 MB could be reclaimed.
```

## How it works

Two-pass scan keeps it fast on big folders:
1. **Group by file size** (cheap) — files with unique sizes can't be duplicates.
2. **Hash only the same-size files** with SHA-256 (1 MB chunks, low memory).

## Options

| Flag | Default | Meaning |
|---|---|---|
| `folder` | — | Directory to scan (required) |
| `--min-size` | `1B` | Skip smaller files (`1KB`, `5MB`, `2GB`) |
| `--ext` | all | Only these extensions, e.g. `.mp4,.mov` |
| `--top N` | all | Show only the N biggest groups |

## Safety notes

- Read-only: no `--delete` flag exists on purpose. Review the list, then delete
  by hand (or move to trash) once you're sure.
- Follows the files you can already read; skips unreadable ones silently.
- Symlinks are hashed by target content like regular files.

MIT-licensed snippet — do whatever you want with it.
