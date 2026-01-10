import feedparser
from feedgen.feed import FeedGenerator
import time
import re

####################################################################################
# VARIABLES - Can be changed to customize script behavior
####################################################################################
sources = [
    "https://vcdx200.uw.cz/feeds/posts/default",
    "https://linux.uw.cz/feeds/posts/default",
    "https://freebsd.uw.cz/feeds/posts/default",
    "https://itkb.uw.cz/feeds/posts/default",
    "https://philosophy.uw.cz/feeds/posts/default",
    "https://itc-bohemians.blogspot.com//feeds/posts/default"
]

max_items = 10000
TITLE="Aggregated RSS feed from all uw.cz blogs"

####################################################################################
# GLOBAL VARIABLES - Do not change them
####################################################################################
items = []

####################################################################################
# FUNCTIONS
####################################################################################
def get_pubdate(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return time.strftime("%Y-%m-%d", entry.published_parsed)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return time.strftime("%Y-%m-%d", entry.updated_parsed)
    return ""

####################################################################################
# MAIN CODE - file generation
####################################################################################

#################################
# --- Get items from RSS sources ---
#################################
for base_url in sources:
    start = 1
    while True:
        url = f"{base_url}?start-index={start}&max-results=50"
        feed = feedparser.parse(url)

        if not feed.entries:
            break

        items.extend(feed.entries)
        start += 50

# Seřadit podle data publikace
items.sort(key=lambda e: e.get("published_parsed", time.gmtime(0)), reverse=True)

#################################
# --- Generate RSS feed ---
#################################
fg = FeedGenerator()
fg.title(TITLE)
fg.link(href="http://localhost/rss", rel="self")
fg.description("Aggreagted RSS feed from all blog posts from uw.cz")

for entry in items[:max_items]:
    fe = fg.add_entry()
    fe.title(entry.title)
    fe.link(href=entry.link)
    fe.description(getattr(entry, "summary", ""))
    fe.pubDate(entry.published if hasattr(entry, "published") else None)

fg.rss_file("/usr/share/nginx/html/combined.xml")

#################################
# --- Generate HTML ---
#################################
html_content = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>{TITLE}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 800px; margin: auto; }}
h1 {{ text-align: center; }}
article {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
a {{ text-decoration: none; color: #0066cc; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>{TITLE}</h1>
"""

article_id = 0
for entry in items[:max_items]:
    article_id += 1
    title = entry.title
    link = entry.link
    pub_date = get_pubdate(entry)
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

    html_content += f'<article data-article-id="{article_id}">\n<h2><a href="{link}">{title}</a></h2>\n<h3>{pub_date}</h3>\n{summary_filtered}\n</article>\n'

html_content += "</body>\n</html>"

# Uložit do HTML souboru
with open("/usr/share/nginx/html/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
