import feedparser
from feedgen.feed import FeedGenerator
import time
import re
from datetime import datetime, timezone
import time
import os

####################################################################################
# VARIABLES - Can be changed to customize script behavior
####################################################################################

# RSS Sources
sources = [
    "https://vcdx200.uw.cz/feeds/posts/default",
    "https://linux.uw.cz/feeds/posts/default",
    "https://freebsd.uw.cz/feeds/posts/default",
    "https://itkb.uw.cz/feeds/posts/default",
    "https://philosophy.uw.cz/feeds/posts/default",
    "https://itc-bohemians.blogspot.com//feeds/posts/default"
]

# Title to be used in generated files
TITLE = "Aggregated RSS feed from all uw.cz blogs"

# BLOG URL to be used in RSS Feed (OUTPUT_RSS_FILE) and Web Page File (OUTPUT_HTML_FILE)
BLOG_URL = "https://blog.uw.cz/"


####################################################################################
# GLOBAL VARIABLES - Do not change them
####################################################################################
items = []
OUTPUT_DIRECTORY = "/usr/share/nginx/html"
OUTPUT_RSS_FILE  = "rss.xml"
OUTPUT_HTML_FILE = "index.html"

####################################################################################
# FUNCTIONS
####################################################################################
def get_pubdate(entry):
    """
    Returns publication date as UTC datetime or None
    """
    parsed = (
        getattr(entry, "published_parsed", None)
        or getattr(entry, "updated_parsed", None)
    )

    if not parsed:
        return None

    return datetime.fromtimestamp(
        time.mktime(parsed),
        tz=timezone.utc
    )

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
fg.link(href=BLOG_URL)
fg.description(TITLE)

for entry in items:
    fe = fg.add_entry()
    fe.title(entry.title)
    fe.link(href=entry.link)
    fe.description(getattr(entry, "summary", ""))
    dt = get_pubdate(entry)
    if dt:
        fe.pubDate(dt)

# Store RSS CONTENT to RSS file
RSS_FILE = os.path.join(OUTPUT_DIRECTORY, OUTPUT_RSS_FILE)
print("RSS File: " + RSS_FILE)
fg.rss_file(RSS_FILE)

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
h2 {{ text-align: center; }}
h3 {{ text-align: center; }}
article {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
a {{ text-decoration: none; color: #0066cc; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>{TITLE}</h1>
<h3>RSS Feed: <a href="{BLOG_URL}/{OUTPUT_RSS_FILE}">{BLOG_URL}/{OUTPUT_RSS_FILE}</a></h3>
<hr>
"""

article_id = 0
for entry in items:
    article_id += 1
    title = entry.title
    link = entry.link
    dt = get_pubdate(entry)
    dt = (
        f'<time datetime="{dt.isoformat()}">{dt.strftime("%A, %B %-d, %Y")}</time>'
        if dt else ""
    )

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

    html_content += f'<article data-article-id="{article_id}">\n<h2><a href="{link}">{title}</a></h2>\n<h3>{dt}</h3>\n{summary_filtered}\n</article>\n'

html_content += "</body>\n</html>"

# Store HTML CONTENT to HTML file
HTML_FILE = os.path.join(OUTPUT_DIRECTORY, OUTPUT_HTML_FILE)
print("HTML File: " + HTML_FILE)
with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)
