import feedparser
from feedgen.feed import FeedGenerator
import time
import re

sources = [
    "https://vcdx200.uw.cz/feeds/posts/default",
    "https://linux.uw.cz/feeds/posts/default",
    "https://freebsd.uw.cz/feeds/posts/default",
    "https://itkb.uw.cz/feeds/posts/default",
    "https://philosophy.uw.cz/feeds/posts/default",
    "https://itc-bohemians.blogspot.com//feeds/posts/default"
]

items = []
max_items = 1000

for url in sources:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        items.append(entry)

# Seřadit podle data publikace
items.sort(key=lambda e: e.get("published_parsed", time.gmtime(0)), reverse=True)

# --- Vytvoření RSS feedu ---
fg = FeedGenerator()
fg.title("blog.uw.cz - aggregated RSS feed")
fg.link(href="http://localhost/rss", rel="self")
fg.description("Aggreagted RSS feed from all blog posts from uw.cz")

for entry in items[:max_items]:
    fe = fg.add_entry()
    fe.title(entry.title)
    fe.link(href=entry.link)
    fe.description(getattr(entry, "summary", ""))
    fe.pubDate(entry.published if hasattr(entry, "published") else None)

fg.rss_file("/usr/share/nginx/html/combined.xml")

# --- Generování HTML ---
html_content = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Aggreagted RSS feed from all uw.cz blogs</title>
<style>
body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; }
h1 { text-align: center; }
article { margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }
a { text-decoration: none; color: #0066cc; }
a:hover { text-decoration: underline; }
</style>
</head>
<body>
<h1>Aggreagted RSS feed from all uw.cz blogs</h1>
"""

for entry in items[:max_items]:
    title = entry.title
    link = entry.link
    summary = getattr(entry, "summary", "")

    # Zobrazit pouze obsah před <a name="more"></a>
    if '<a name="more"></a>' in summary:
        summary = summary.split('<a name="more"></a>')[0]

    # Povolené tagy: <img>, <p>, <br>
    def filter_html(match):
        tag = match.group(0)
        if tag.startswith('<img') or tag.startswith('<p') or tag.startswith('</p') or tag.startswith('<br'):
            return tag
        return ''  # ostatní tagy odstraníme

    summary_filtered = re.sub(r'<[^>]+>', filter_html, summary)

    html_content += f'<article>\n<h2><a href="{link}">{title}</a></h2>\n{summary_filtered}\n</article>\n'

html_content += "</body>\n</html>"

# Uložit do HTML souboru
with open("/usr/share/nginx/html/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

