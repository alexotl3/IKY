#!/usr/bin/env python3
"""
Checks https://www.iky.gr/ypotrofies/ for new announcements and posts
any new ones to a Discord channel via webhook.

State (which posts have already been seen) is stored in seen_posts.json
in this same repo, so the GitHub Action can commit updates to it.
"""

import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://www.iky.gr/ypotrofies/"
STATE_FILE = Path(__file__).parent / "seen_posts.json"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

HEADERS = {
    # A normal browser User-Agent avoids some basic bot-blocking.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# The section on the page is introduced by this heading text.
SECTION_HEADING = "Ανακοινώσεις Υποτροφίες"
# The section ends at a "load more" link with this text.
SECTION_END_TEXT = "Περισσότερα"


def fetch_announcements():
    """Scrape the page and return a list of dicts: {title, url}."""
    resp = requests.get(PAGE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the heading that introduces the announcements section.
    heading = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        if SECTION_HEADING in tag.get_text():
            heading = tag
            break

    if heading is None:
        raise RuntimeError(
            "Could not find the announcements section heading on the page. "
            "The site's layout may have changed."
        )

    posts = []
    seen_urls = set()

    # Walk forward through the following elements in document order,
    # collecting links that look like announcement titles, until we
    # hit the "Περισσότερα" (load more) link, which marks the end of
    # this section.
    for el in heading.find_all_next():
        text = el.get_text(strip=True) if hasattr(el, "get_text") else ""
        if el.name == "a" and SECTION_END_TEXT in text:
            break

        if el.name == "a":
            href = el.get("href", "")
            title = el.get_text(strip=True)
            # Skip empty links, anchors, images-only links, nav links, etc.
            if not href or not title:
                continue
            if not href.startswith("https://www.iky.gr/"):
                continue
            if href in seen_urls:
                continue
            # Heuristic: real announcement titles are reasonably long.
            if len(title) < 15:
                continue
            seen_urls.add(href)
            posts.append({"title": title, "url": href})

    return posts


def load_seen():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(urls):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, ensure_ascii=False, indent=2)


def post_to_discord(post):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL environment variable is not set.")

    payload = {
        "content": f"📢 **Νέα ανακοίνωση υποτροφιών ΙΚΥ**\n{post['title']}\n{post['url']}"
    }
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30)
    resp.raise_for_status()


def main():
    posts = fetch_announcements()
    if not posts:
        print("No announcements found on the page (check the scraper).")
        sys.exit(1)

    seen = load_seen()
    is_first_run = len(seen) == 0

    new_posts = [p for p in posts if p["url"] not in seen]

    if is_first_run:
        # Don't spam Discord with every historical post on the very
        # first run -- just record everything currently on the page
        # as "already seen" and start fresh from here.
        print(f"First run: recording {len(posts)} existing posts as seen, no Discord messages sent.")
    else:
        # Post oldest-first so the channel reads top-to-bottom chronologically.
        for post in reversed(new_posts):
            print(f"Posting new announcement: {post['title']}")
            post_to_discord(post)

    all_urls = seen | {p["url"] for p in posts}
    save_seen(all_urls)

    if not is_first_run:
        print(f"Done. {len(new_posts)} new post(s) posted.")


if __name__ == "__main__":
    main()
