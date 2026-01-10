# RSS Feed Aggregator

It reads feeds from various RSS sources and generates aggregated Web Page (./html/index.html) and RSS Feeed (./html/combined.xml)

Customization variables __RSS Sources__ and __Title__ are defined at the beginning of python script.

```code
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
TITLE="Aggregated RSS feed from all uw.cz blogs"
```
