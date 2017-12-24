#!/usr/bin/env python
# -*- coding: utf-8 -*-

import articles
import feeds
import podcasts


class PodcastBuilder(object):
    podcast_items = []
    location = None

    def __init__(self, url, slug):
        self.url = url
        self.slug = slug

    def build(self):
        self.__parse_feed()
        self.__render_articles()
        self.__build_podcast()
        self.__write_podcast()
        self.location = self.__upload_podcast()
        self.__clean_up_podcast()

        return self.location

    def __parse_feed(self):
        self.feed = feeds.Feed(self.url)
        self.feed.parse()

    def __render_articles(self):
        for item in self.feed.items:
            audio_article = articles.AudioArticle(text=item.description.text, title=item.title)
            audio_article.render()

            podcast_item = podcasts.PodcastItem(item, audio_article)
            self.podcast_items.append(podcast_item)

    def __build_podcast(self):
        self.podcast = podcasts.Podcast(self.slug, self.podcast_items)
        self.podcast.title = self.feed.title
        self.podcast.link = self.feed.link
        self.podcast.id = self.feed.link
        # TODO: Fetch author from the feed
        self.podcast.author = 'John Doe'
        self.podcast.title = self.feed.title
        self.podcast.title = self.feed.title

        return self.podcast.build()

    def __write_podcast(self):
        return self.podcast.write()

    def __upload_podcast(self):
        return self.podcast.upload()

    def __clean_up_podcast(self):
        return self.podcast.clean_up()

# url = "https://themerkle.com/feed/"
# slug = "themerkle"
# pb = PodcastBuilder(url, slug)
# location = pb.build()
# print(location)
