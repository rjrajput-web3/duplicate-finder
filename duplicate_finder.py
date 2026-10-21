#!/usr/bin/env python3
"""
duplicate_finder.py — Find duplicate files by content hash.

Scans a directory (recursively) and groups files that are byte-identical,
using a fast size pre-filter followed by SHA-256 hashing, so only real
duplicates get hashed. Never deletes anything on its own — use --move to
quarantine suspected duplicates into a folder for manual review.

Usage:
    python3 duplicate_finder.py /path/to/folder
    python3 duplicate_finder.py /path/to/folder --min-size 1048576
    python3 duplicate_finder.py /path/to/folder --json duplicates.json
    python3 duplicate_finder.py /path/to/folder --move ~/dupes-to-review

Options:
    --min-size BYTES   Skip files smaller than this (default 1)
    --json PATH        Also write the duplicate groups to a JSON file
    --move DIR         Copy duplicate copies (keeping the first of each
                       group) into DIR for review. Nothing is deleted.
    --extensions exts  Comma-separated list, e.g. --extensions jpg,png,mp4
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict

CHUNK = 1024 * 1024  # 1 MB read chunks


def sha256_of(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                h.update(chunk)
    except (OSError, PermissionError):
        return None
    return h.hexdigest()


def collect_files(root, min_size, extensions):
    paths = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if extensions and not name.lower().endswith(tuple(extensions)):
                continue
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size >= min_size:
                paths.append((full, size))
    return paths


def find_duplicates(root, min_size=1, extensions=None):
    files = collect_files(root, min_size, extensions)

    # Size pre-filter: files with a unique size can't be duplicates.
    by_size = defaultdict(list)
    for path, size in files:
        by_size[size].append(path)

    groups = []
    scanned = 0
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue
        by_hash = defaultdict(list)
        for path in candidates:
            digest = sha256_of(path)
            scanned += 1
            if digest:
                by_hash[digest].append(path)
        for digest, dupes in by_hash.items():
            if len(dupes) > 1:
                groups.append({"sha256": digest, "size": size,
                               "files": sorted(dupes)})

    groups.sort(key=lambda g: (-g["size"], g["files"][0]))
    return groups, scanned, len(files)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    ap = argparse.ArgumentParser(description="Find duplicate files by SHA-256 content hash.")
    ap.add_argument("directory", help="Folder to scan (recursive).")
    ap.add_argument("--min-size", type=int, default=1,
                    help="Skip files smaller than this many bytes (default 1).")
    ap.add_argument("--json", metavar="PATH", default=None,
                    help="Write duplicate groups to a JSON file.")
    ap.add_argument("--move", metavar="DIR", default=None,
                    help="Copy extra copies (keeping the first of each group) "
                         "into DIR for review. Nothing is deleted.")
    ap.add_argument("--extensions", default=None,
                    help="Comma-separated extensions to scan, e.g. jpg,png,mp4.")
    args = ap.parse_args()

    if not os.path.isdir(args.directory):
        print(f"error: not a directory: {args.directory}", file=sys.stderr)
        return 2

    exts = None
    if args.extensions:
        exts = ["." + e.strip().lstrip(".").lower()
                for e in args.extensions.split(",")]

    groups, scanned, total = find_duplicates(args.directory, args.min_size, exts)

    wasted = sum(g["size"] * (len(g["files"]) - 1) for g in groups)
    print(f"Scanned {scanned} candidate files ({total} total).")
    if not groups:
        print("No duplicates found.")
    else:
        print(f"Found {len(groups)} duplicate group(s), "
              f"{human(wasted)} reclaimable:")
        for i, g in enumerate(groups, 1):
            print(f"\n[{i}] {human(g['size'])} each, {len(g['files'])} copies:")
            for path in g["files"]:
                print(f"    {path}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(groups, f, indent=2)
        print(f"\nWrote {args.json}")

    if args.move and groups:
        os.makedirs(args.move, exist_ok=True)
        copied = 0
        for g in groups:
            for path in g["files"][1:]:  # keep the first copy in place
                target = os.path.join(args.move, os.path.basename(path))
                n, base = 1, target
                while os.path.exists(target):  # avoid name collisions
                    root, ext = os.path.splitext(base)
                    target = f"{root}-{n}{ext}"
                    n += 1
                shutil.copy2(path, target)
                copied += 1
        print(f"Copied {copied} duplicate copies to {args.move} "
              f"(originals untouched).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
