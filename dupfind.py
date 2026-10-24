#!/usr/bin/env python3
"""duplicate-finder: find duplicate files by content hash.

Walks a directory tree, groups files with identical SHA-256 hashes,
and prints each duplicate group with total wasted space.
Report-only by default -- never deletes anything.

Usage:
    python3 dupfind.py /path/to/folder
    python3 dupfind.py /path/to/folder --min-size 1MB --ext .mp4,.mov
    python3 dupfind.py /path/to/folder --top 10
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict


def parse_size(text):
    text = text.strip().upper()
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    for suffix, mult in sorted(units.items(), key=lambda x: -len(x[0])):
        if text.endswith(suffix):
            return int(float(text[: -len(suffix)]) * mult)
    return int(text)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024


def hash_file(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def find_duplicates(root, min_size=0, exts=None):
    """Two-pass scan: group by size first (cheap), hash only same-size files."""
    by_size = defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if exts and not any(name.lower().endswith(e) for e in exts):
                continue
            path = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if size >= min_size:
                by_size[size].append(path)

    groups = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash = defaultdict(list)
        for path in paths:
            try:
                by_hash[hash_file(path)].append(path)
            except OSError:
                continue
        for digest, dupes in by_hash.items():
            if len(dupes) > 1:
                groups.append((size, digest, sorted(dupes)))
    return sorted(groups, key=lambda g: g[0] * (len(g[2]) - 1), reverse=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find duplicate files by SHA-256 hash.")
    ap.add_argument("folder", help="Directory to scan")
    ap.add_argument("--min-size", default="1B",
                    help="Ignore files smaller than this (e.g. 1KB, 5MB). Default: 1B")
    ap.add_argument("--ext", default="",
                    help="Comma-separated extensions to include, e.g. .mp4,.mov")
    ap.add_argument("--top", type=int, default=0,
                    help="Show only the top N biggest duplicate groups (0 = all)")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.folder)
    if not os.path.isdir(root):
        print(f"Error: not a directory: {root}", file=sys.stderr)
        return 2

    exts = [e.strip().lower() for e in args.ext.split(",") if e.strip()] or None
    groups = find_duplicates(root, min_size=parse_size(args.min_size), exts=exts)

    if not groups:
        print("No duplicate files found.")
        return 0

    total_wasted = 0
    shown = groups[: args.top] if args.top else groups
    for i, (size, digest, paths) in enumerate(shown, 1):
        wasted = size * (len(paths) - 1)
        total_wasted += wasted
        print(f"[{i}] {len(paths)} copies x {human(size)} = {human(wasted)} wasted "
              f"(sha256:{digest[:12]}...)")
        for p in paths:
            print(f"      {p}")

    if args.top and len(groups) > args.top:
        print(f"... and {len(groups) - args.top} more groups not shown.")
    print(f"\n{len(groups)} duplicate groups, ~{human(total_wasted)} could be reclaimed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
