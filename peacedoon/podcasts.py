#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from datetime import timezone
from time import mktime

from dateutil import tz
from feedgen.feed import FeedGenerator

import settings
import uploader


class Podcast(object):
    id = None
    title = None
    author = None
    link = None
    logo = None
    body = None
    subtitle = '-'
    language = 'en'

    def __init__(self, slug, items=[]):
        self.slug = slug
        self.items = items

    def build(self):
        fg = FeedGenerator()

        fg.id(self.id)
        fg.title(self.title)
        # TODO: Get actual author, categories, etc details from the feed
        fg.author({'name': self.author, 'email': 'john@example.com'})
        fg.link(href=self.link, rel='alternate')
        fg.logo(self.logo)
        fg.subtitle(self.subtitle)
        fg.language(self.language)

        fg.load_extension('podcast', rss=True)
        fg.podcast.itunes_category('Technology', 'Podcasting')
        fg.podcast.itunes_summary(self.subtitle)
        # TODO: Add podcast image covers, both standard RSS and Itune-compatible

        for item in self.items:
            fe = fg.add_entry()
            fe.id(item.id)
            fe.title(item.title)
            fe.description(item.description)
            # fe.description('Enjoy our first episode.')
            fe.pubdate(item.published_at)

            file_name = os.path.basename(item.file)
            file_location = "%s/%s/%s" % (settings.S3_HTTP_PREFIX, self.slug, file_name)
            file_size = str(os.path.getsize(item.file)).encode("utf-8").decode("utf-8")
            fe.enclosure(file_location, file_size, 'audio/mpeg')

        self.body = fg.rss_str(pretty=True).decode("utf-8")

    def __save_path(self):
        filename = "%s.xml" % self.slug
        return os.path.abspath(os.path.join(settings.TMP_DIR, filename))

    def write(self):
        text_file = open(self.__save_path(), "w")
        text_file.write(self.body)
        text_file.close()

    def upload(self):
        xml_uploader = uploader.Uploader(self.__save_path(), s3_filepath=self.slug)
        xml_url = xml_uploader.upload()

        # Uploading each MP3 file
        for item in self.items:
            mp3_uploader = uploader.Uploader(item.file, s3_filepath=self.slug)
            mp3_url = mp3_uploader.upload()

        return xml_url

    def clean_up(self):
        """Clean up local MP3 and XML"""

        # Clean up MP3 files
        [x.audio_article.clean_up() for x in self.items]

        # Clean up XML
        os.remove(self.__save_path())


class PodcastItem(object):
    """Article class stores both parsed RSS feed and appropriate audio article"""

    def __init__(self, feed_item, audio_article):
        self.feed_item = feed_item
        self.audio_article = audio_article

        self.__assign_attributes()

    def __assign_attributes(self):
        self.id = self.feed_item.id
        self.title = self.feed_item.title
        self.description = self.feed_item.description.text
        self.file = self.audio_article.audiofile

        self.published_at = datetime.now(timezone.utc)
        if self.feed_item.published_at:
            published_dt = datetime.fromtimestamp(mktime(self.feed_item.published_at))
            to_zone = tz.gettz('UTC')
            self.published_at = published_dt.astimezone(to_zone)
