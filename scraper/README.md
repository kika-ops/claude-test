# Article scraper

Collects the articles from a website (by default the Ministry of Equipment and
Water, `equipement.gov.ma`) and saves them as Markdown files, for exam practice.

## Setup (one time)

1. Install Python 3 from https://www.python.org/downloads/ (on Windows, tick
   "Add Python to PATH" during install).
2. Open a terminal in this `scraper` folder and run:

   ```
   pip install -r requirements.txt
   ```

## Run

```
python scrape.py
```

Useful options:

| Option | Example | What it does |
|---|---|---|
| `--max-pages` | `--max-pages 500` | How many pages to visit (default 300) |
| `--keywords` | `--keywords "الماء,السدود,تحلية"` | Keep only articles containing one of these words |
| `--start` | `--start https://www.marocmeteo.ma/` | Scrape another site |
| `--out` | `--out articles_eau` | Output folder (default `articles`) |
| `--delay` | `--delay 2` | Seconds between requests (default 1) |

Press `Ctrl+C` to stop early; what was already collected is kept.

## Output

In the `articles` folder:

- `0001-....md`, `0002-....md`: one file per article (title, link, date, text)
- `all_articles.md`: all the articles in one file
- `index.csv`: list of articles (opens in Excel)
- `pdf_links.txt`: links to PDF documents found on the site (strategies,
  reports), to download by hand
