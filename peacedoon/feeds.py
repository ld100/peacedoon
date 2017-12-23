import feedparser
from bs4 import BeautifulSoup


class Feed:
    """Simple object representation of RSS/ATOM feed"""

    def __init__(self, url=None, language='english'):
        self.items = []
        self.title = None
        self.description = None
        self.url = url
        self.link = url
        self.language = language
        self.image = None
        self.author = None

    def parse(self):
        feed = feedparser.parse(self.url)
        self.title = feed['feed']['title']
        if 'language' in feed:
            self.language = feed['language']

        if 'image' in feed:
            self.image = feed['image']['href']

        if 'description' in feed:
            self.description = feed['description']

        if 'author_detail' in feed:
            self.author = feed['author_detail']

        for entry in feed.entries:
            # article_published_at = entry.published  # Unicode string
            description = entry.description
            if "content" in entry and len(entry["content"]) > 0:
                description = entry.content[0]["value"]
                # import json
                # print(json.dumps(description, sort_keys=True, indent=4))

            item = FeedItem(
                entry.id,
                entry.title,
                entry.link,
                description,
                entry.author,
                entry.published_parsed  # Time object
            )
            self.items.append(item)


class FeedItem:
    """Object representation of RSS/ATOM feed item"""

    def __init__(self, id, title, link, description, author, published_at):
        self.id = id
        self.title = title
        self.link = link
        self.description = ItemDescription(description)
        self.description_text = str(self.description)
        self.author = author
        self.published_at = published_at


class ItemDescription:
    def __init__(self, description):
        self.html = description
        self.text = BeautifulSoup(description, 'html.parser').text

    def __repr__(self):
        return self.text

    def __str__(self):
        return self.text
