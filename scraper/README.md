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

## Rank the articles like the exam jury

After scraping, run:

```
python rank.py
python rank.py --folder eau --top 20
```

Each article gets a score based on the traits of the 2025 exam text (which was
copied word for word from an official policy page): 300 to 600 words, at least
5 paragraphs, reference to the King's guidance, strategy and governance
vocabulary, a law reference, logical connectors, few figures, and no event-news
tone (visits, inaugurations, meetings). The 2025 exam text itself scores 22 out
of 23. The best articles are printed first, and the full list is saved to
`ranking.csv` in the same folder.
