"""Generate seed_data.json from the arXiv API — no large downloads needed.

Usage:
    pip install requests
    cd api
    python generate_seed.py

Fetches CS paper metadata directly from arXiv API in small batches.
No Kaggle account, no 5GB downloads, no GCS buckets.
"""

from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict

import requests

OUTPUT_FILE = "seed_data.json"
BASE_URL = "http://export.arxiv.org/api/query"

# arXiv CS categories to fetch, mapped to friendly names
CATEGORIES = {
    "cs.AI": "AI/ML",
    "cs.LG": "AI/ML",
    "cs.CL": "AI/ML",
    "cs.CV": "AI/ML",
    "cs.NE": "AI/ML",
    "cs.SE": "Software Engineering",
    "cs.PL": "Programming Languages",
    "cs.DC": "Distributed Systems",
    "cs.CR": "Security & Crypto",
    "cs.DB": "Databases",
    "cs.NI": "Networking",
    "cs.RO": "Robotics",
    "cs.HC": "HCI",
    "cs.IR": "Information Retrieval",
    "cs.SI": "Social Computing",
    "cs.CY": "Computing Policy",
    "cs.MM": "Multimedia",
    "cs.GT": "Game Theory",
    "cs.AR": "Hardware",
    "cs.CG": "Graphics",
    "cs.DS": "Algorithms",
    "cs.CC": "Complexity",
    "cs.FL": "Formal Methods",
    "cs.LO": "Logic",
    "cs.MA": "Multi-agent",
    "cs.SC": "Symbolic Computation",
    "cs.SD": "Sound",
    "cs.ET": "Emerging Tech",
    "cs.OS": "Operating Systems",
    "cs.PF": "Performance",
    "cs.SY": "Systems & Control",
}

TARGET_PER_CATEGORY = 500
BATCH_SIZE = 200  # max per API request
MIN_ABSTRACT_LEN = 80
MAX_ABSTRACT_LEN = 1200
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def clean_text(text: str) -> str:
    text = re.sub(r"\$[^$]+\$", "", text)
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"[{}~^]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_batch(cat: str, start: int, max_results: int) -> list[dict]:
    """Fetch a batch of papers from arXiv API."""
    query = f"cat:{cat}"
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()

    papers = []
    root = ET.fromstring(resp.text)
    for entry in root.findall("atom:entry", NS):
        title = clean_text(entry.findtext("atom:title", "", NS))
        abstract = clean_text(entry.findtext("atom:summary", "", NS))

        # Get arxiv ID from the URL
        id_url = entry.findtext("atom:id", "", NS)
        arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else ""

        # Get categories
        cats = []
        for cat_el in entry.findall("atom:category", NS):
            term = cat_el.get("term", "")
            if term:
                cats.append(term)

        papers.append({
            "title": title,
            "abstract": abstract,
            "arxiv_id": arxiv_id,
            "categories": cats,
        })

    return papers


def extract_tags(categories: list[str]) -> list[str]:
    tags = []
    for cat in categories:
        if cat.startswith("cs."):
            tags.append(cat.split(".")[-1].lower())
    return tags[:4]


def main():
    buckets: dict[str, list[dict]] = defaultdict(list)
    seen_titles = set()

    for arxiv_cat, friendly_cat in sorted(CATEGORIES.items()):
        if len(buckets[friendly_cat]) >= TARGET_PER_CATEGORY:
            continue

        print(f"\nFetching {arxiv_cat} → {friendly_cat}...")
        start = 0
        cat_collected = 0
        needed = TARGET_PER_CATEGORY - len(buckets[friendly_cat])

        while cat_collected < needed:
            try:
                batch = fetch_batch(arxiv_cat, start, BATCH_SIZE)
            except requests.RequestException as e:
                print(f"  API error: {e}, retrying in 5s...")
                time.sleep(5)
                continue

            if not batch:
                print(f"  No more papers available for {arxiv_cat}")
                break

            for paper in batch:
                title = paper["title"]
                abstract = paper["abstract"]

                if len(title) < 10 or len(abstract) < MIN_ABSTRACT_LEN or len(abstract) > MAX_ABSTRACT_LEN:
                    continue
                if title in seen_titles:
                    continue

                seen_titles.add(title)
                tags = extract_tags(paper["categories"])
                description = abstract[:600].rsplit(" ", 1)[0]
                if len(abstract) > 600:
                    description += "..."

                buckets[friendly_cat].append({
                    "title": title,
                    "description": description,
                    "category": friendly_cat,
                    "tags": tags if tags else ["cs"],
                    "url": f"https://arxiv.org/abs/{paper['arxiv_id']}",
                })
                cat_collected += 1

            start += len(batch)
            total = sum(len(v) for v in buckets.values())
            print(f"  {arxiv_cat}: {cat_collected} collected | Total: {total}")

            # arXiv asks to respect rate limits
            time.sleep(3)

    articles = []
    for cat in sorted(buckets.keys()):
        articles.extend(buckets[cat])

    print(f"\nCollected {len(articles)} articles across {len(buckets)} categories:")
    for cat in sorted(buckets.keys()):
        print(f"  {cat}: {len(buckets[cat])}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"\nWritten to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
