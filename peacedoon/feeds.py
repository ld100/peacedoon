import feedparser
from bs4 import BeautifulSoup


class Feed:
    """Simple object representation of RSS/ATOM feed"""

    def __init__(self, url=None):
        self.items = []
        self.title = None
        self.url = url

    def parse(self):
        feed = feedparser.parse(self.url)
        self.title = feed['feed']['title']

        for entry in feed.entries:
            # article_published_at = entry.published  # Unicode string
            item = FeedItem(
                entry.title,
                entry.link,
                entry.description,
                entry.author,
                entry.published_parsed  # Time object
            )
            self.items.append(item)


class FeedItem:
    """Object representation of RSS/ATOM feed item"""

    def __init__(self, title, link, description, author, published_at):
        self.title = title
        self.link = link
        self.description_html = description
        self.description_text = BeautifulSoup(description, 'html.parser').text
        self.author = author
        self.published_at = published_at