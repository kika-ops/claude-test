#!/usr/bin/env python3
"""Crawl a website and save its articles as Markdown files.

Built to collect articles from the Ministry of Equipment and Water website
(equipement.gov.ma) for exam practice, but works on any site.

Usage:
    python scrape.py
    python scrape.py --max-pages 500 --keywords "الماء,السدود,تحلية"
    python scrape.py --start https://www.marocmeteo.ma/
"""
import argparse
import csv
import hashlib
import re
import time
from collections import deque
from pathlib import Path
from urllib import robotparser
from urllib.parse import urldefrag, urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

DEFAULT_START = ["https://www.equipement.gov.ma/"]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; article-collector)"}
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".css", ".js",
    ".zip", ".rar", ".mp3", ".mp4", ".avi", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx",
}


def normalize(url):
    url, _ = urldefrag(url)
    return url.rstrip("/")


def host_variants(url):
    host = urlparse(url).netloc.lower()
    bare = host[4:] if host.startswith("www.") else host
    return {bare, "www." + bare}


def load_robots(session, hosts, scheme="https"):
    parsers = {}
    for host in hosts:
        parser = robotparser.RobotFileParser()
        try:
            response = session.get(f"{scheme}://{host}/robots.txt", timeout=15)
            parser.parse(response.text.splitlines() if response.ok else [])
        except requests.RequestException:
            parser.parse([])
        parsers[host] = parser
    return parsers


def can_fetch(parsers, url):
    parser = parsers.get(urlparse(url).netloc.lower())
    return parser is None or parser.can_fetch(HEADERS["User-Agent"], url)


def extract_article(html, url):
    text = trafilatura.extract(html, url=url, include_comments=False,
                               include_tables=False, favor_precision=True) or ""
    metadata = trafilatura.extract_metadata(html, default_url=url)
    title = metadata.title if metadata and metadata.title else ""
    date = metadata.date if metadata and metadata.date else ""
    if not title:
        tag = BeautifulSoup(html, "html.parser").title
        title = tag.get_text(strip=True) if tag else url
    return title, date, text


def file_name(index, title):
    slug = re.sub(r"[^\w\-]+", "-", title, flags=re.UNICODE).strip("-")[:60]
    return f"{index:04d}-{slug or 'article'}.md"


def page_links(html, base_url):
    for anchor in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        link = urljoin(base_url, anchor["href"].strip())
        if link.startswith(("http://", "https://")):
            yield normalize(link)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", nargs="+", default=DEFAULT_START,
                        help="start URL(s); only links on the same site are followed")
    parser.add_argument("--max-pages", type=int, default=300,
                        help="maximum number of pages to visit (default: 300)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="seconds to wait between requests (default: 1)")
    parser.add_argument("--min-words", type=int, default=150,
                        help="skip pages with fewer words than this (default: 150)")
    parser.add_argument("--keywords", default="",
                        help="comma-separated words; keep only articles containing one of them")
    parser.add_argument("--out", default="articles", help="output folder (default: articles)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    keywords = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]

    session = requests.Session()
    session.headers.update(HEADERS)

    starts = [normalize(url) for url in args.start]
    hosts = set().union(*(host_variants(url) for url in starts))
    robots = load_robots(session, hosts, urlparse(starts[0]).scheme)

    queue = deque(starts)
    seen = set(starts)
    seen_texts = set()
    pdf_links = set()
    visited = saved = 0

    index_file = open(out_dir / "index.csv", "w", newline="", encoding="utf-8-sig")
    index = csv.writer(index_file)
    index.writerow(["file", "title", "date", "words", "url"])
    combined = open(out_dir / "all_articles.md", "w", encoding="utf-8")

    try:
        while queue and visited < args.max_pages:
            url = queue.popleft()
            if not can_fetch(robots, url):
                continue
            try:
                response = session.get(url, timeout=20)
            except requests.RequestException as error:
                print(f"  ! {url}: {error}")
                continue
            visited += 1
            time.sleep(args.delay)

            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" in content_type:
                pdf_links.add(url)
                continue
            if not response.ok or "html" not in content_type:
                continue
            if not response.encoding or response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding
            html = response.text

            for link in page_links(html, response.url):
                path = urlparse(link).path.lower()
                if path.endswith(".pdf"):
                    pdf_links.add(link)
                elif (link not in seen and urlparse(link).netloc.lower() in hosts
                      and Path(path).suffix not in SKIP_EXTENSIONS):
                    seen.add(link)
                    queue.append(link)

            title, date, text = extract_article(html, response.url)
            words = len(text.split())
            if words < args.min_words:
                continue
            if keywords and not any(k in (title + " " + text).lower() for k in keywords):
                continue
            digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
            if digest in seen_texts:
                continue
            seen_texts.add(digest)

            saved += 1
            name = file_name(saved, title)
            article = f"# {title}\n\n- URL: {response.url}\n- Date: {date or '?'}\n\n{text}\n"
            (out_dir / name).write_text(article, encoding="utf-8")
            combined.write(article + "\n---\n\n")
            index.writerow([name, title, date, words, response.url])
            print(f"[{visited}/{args.max_pages}] saved {name} ({words} words)")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        index_file.close()
        combined.close()
        (out_dir / "pdf_links.txt").write_text("\n".join(sorted(pdf_links)) + "\n",
                                                encoding="utf-8")

    print(f"\nDone: visited {visited} pages, saved {saved} articles, "
          f"found {len(pdf_links)} PDF links. Output: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
