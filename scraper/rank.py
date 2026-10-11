#!/usr/bin/env python3
"""Rank collected articles by how closely they match the exam jury's choices.

The 2025 exam text was copied word for word from an official policy page. This
script scores each article saved by scrape.py against the traits of that text:
length, paragraph structure, royal and strategic anchoring, governance and
legal vocabulary, logical connectors, few figures, and no event-news tone.

Usage:
    python rank.py
    python rank.py --folder eau --top 20
"""
import argparse
import csv
import re
from pathlib import Path

# Each family: (label, keywords, points per distinct match, max points)
FAMILIES = [
    ("royal", ["جلالة الملك", "التوجيهات الملكية", "القيادة الرشيدة", "الخطاب الملكي",
               "الرؤية الملكية", "sa majesté", "hautes orientations royales",
               "discours royal", "vision royale"], 3, 3),
    ("strategy", ["استراتيجية", "النموذج التنموي", "البرنامج الحكومي", "خارطة طريق",
                  "برنامج وطني", "البرنامج الوطني", "مخطط", "أفق 2030", "أفق 2040", "رؤية",
                  "stratégie", "nouveau modèle de développement", "programme gouvernemental",
                  "feuille de route", "programme national", "horizon 2030", "horizon 2040"], 1, 3),
    ("governance", ["الحكامة", "النجاعة", "الشفافية", "تبسيط المساطر", "اللاتمركز",
                    "الجهوية المتقدمة", "المرتفق", "جودة الخدمات", "المرافق العمومية",
                    "المقاربة التشاركية", "الالتقائية", "ربط المسؤولية بالمحاسبة",
                    "gouvernance", "efficacité", "transparence", "simplification des procédures",
                    "déconcentration", "régionalisation avancée", "usagers",
                    "qualité des services", "services publics", "approche participative",
                    "convergence"], 1, 4),
    ("challenges", ["التنمية المستدامة", "التغيرات المناخية", "الأمن المائي", "الإجهاد المائي",
                    "الانتقال الطاقي", "العدالة المجالية", "التحول الرقمي", "الرقمنة",
                    "الذكاء الاصطناعي", "الطاقات المتجددة", "développement durable",
                    "changements climatiques", "changement climatique", "sécurité hydrique",
                    "stress hydrique", "transition énergétique", "équité territoriale",
                    "transformation digitale", "transition numérique", "digitalisation",
                    "intelligence artificielle", "énergies renouvelables"], 1, 3),
    ("connectors", ["وفي هذا السياق", "وفي نفس السياق", "وفي هذا الصدد", "وفي هذا الإطار",
                    "وتماشيا مع", "ومن هذا المنطلق", "كما", "بالإضافة إلى", "فضلا عن",
                    "dans ce cadre", "dans ce contexte", "à cet égard", "par ailleurs",
                    "en outre", "conformément"], 1, 3),
]
NEWS_WORDS = ["تدشين", "زيارة", "ترأس", "حفل", "اجتماع", "ندوة صحفية", "inauguration",
              "visite", "a présidé", "cérémonie", "réunion"]
LAW_PATTERN = re.compile(r"(القانون|قانون|المرسوم|مرسوم|ميثاق|loi|décret|charte)\s*(رقم|n°)?\s*\d",
                         re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")


def read_article(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    url = next((l[len("- URL: "):] for l in lines if l.startswith("- URL: ")), "")
    body = "\n".join(l for l in lines[1:] if not l.startswith("- URL: ")
                     and not l.startswith("- Date: "))
    return title, url, body.strip()


def score(body):
    lower = body.lower()
    words = len(body.split())
    paragraphs = len([p for p in body.split("\n") if len(p.split()) >= 15])
    points, notes = 0, []

    if 300 <= words <= 600:
        points += 3
    elif 200 <= words < 300 or 600 < words <= 900:
        points += 1
    notes.append(f"{words} words")

    if paragraphs >= 5:
        points += 2
    notes.append(f"{paragraphs} paragraphs")

    for label, keywords, each, cap in FAMILIES:
        found = [k for k in keywords if k in lower]
        if found:
            points += min(len(found) * each, cap)
            notes.append(f"{label}: {', '.join(found[:4])}")

    if LAW_PATTERN.search(body):
        points += 2
        notes.append("law reference")

    numbers_per_100 = len(NUMBER_PATTERN.findall(body)) * 100 / max(words, 1)
    if numbers_per_100 > 3:
        points -= 2
        notes.append("many figures")

    news = [w for w in NEWS_WORDS if w in lower]
    if news:
        points -= min(len(news), 3)
        notes.append(f"news tone: {', '.join(news)}")

    return points, words, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--folder", default="articles",
                        help="folder created by scrape.py (default: articles)")
    parser.add_argument("--top", type=int, default=15, help="how many to show (default: 15)")
    args = parser.parse_args()

    folder = Path(args.folder)
    rows = []
    for path in sorted(folder.glob("[0-9]*.md")):
        title, url, body = read_article(path)
        points, words, notes = score(body)
        rows.append((points, path.name, title, words, url, " | ".join(notes)))
    rows.sort(key=lambda row: row[0], reverse=True)

    with open(folder / "ranking.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["score", "file", "title", "words", "url", "why"])
        writer.writerows(rows)

    for points, name, title, words, _, notes in rows[:args.top]:
        print(f"{points:>3}  {name}  {title}\n     {notes}")
    print(f"\nRanked {len(rows)} articles. Full list: {(folder / 'ranking.csv').resolve()}")


if __name__ == "__main__":
    main()
