#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import os

import boto3
import nltk
from feedgen.feed import FeedGenerator
from pydub import AudioSegment
from pyssml.PySSML import PySSML

import feeds
import settings


class AudioArticle:
    """Representation of an auio article: both text and audio-files"""

    def __init__(self, text=None, title=None, voice='Matthew', language='english'):
        # AWS max length
        self.MAX_LENGTH = 1500

        self.text = text
        self.title = self._build_ssml_title(title)
        self.language = language
        self.voice = voice

        self.sentences = []
        self._build_sentences()

        # Build title
        self.sentences = [self.title] + self.sentences

        # We render chunks of text, which are under 1500 chars
        # Due to AWS Polly limitation
        self.chunks = []
        self._build_chunks()
        self._finish_chunks()

        # Path for article audiofile
        self.audiofile = None

    # TODO: Create unique filenames for chunks
    def render(self):
        renderers = []
        for i, e in zip(range(len(self.chunks)), self.chunks):
            filename = "%i.mp3" % i
            chunk = self._render_chunk(e, filename)
            renderers.append(chunk)
            # chunk.clean_up()

        # Glue chunks
        podcast_stream = None
        for renderer in renderers:
            audio_stream = AudioSegment.from_mp3(renderer.file_path)
            if podcast_stream is None:
                podcast_stream = audio_stream
            else:
                podcast_stream += audio_stream

        podcast_filename = "%s.mp3" % self.generate_hash()
        podcast_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp', podcast_filename))

        music_filename = 'looperman-l-2099293-0117520-dylanjake-the-weeknd-type-pad.mp3'
        music_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', music_filename))
        music_stream = AudioSegment.from_mp3(music_path)
        MUSIC_VOLUME = -7
        podcast_stream = podcast_stream.overlay(music_stream + MUSIC_VOLUME, loop=True)

        podcast_stream.export(podcast_path, format="mp3")

        # Clean up the shit
        [x.clean_up() for x in renderers]

        self.audiofile = podcast_path

    def _render_chunk(self, chunk, filename):
        renderer = AudioRenderer(
            text=chunk,
            filename=filename,
            voice=self.voice
        )
        renderer.render()
        # renderer.clean_up()
        return renderer

    # TODO: Check if sentence length is under 1500 chars, split it further otherwise
    def _build_sentences(self):
        """Split the text into sentences"""
        try:
            self.sentences = nltk.sent_tokenize(self.text)
        except LookupError:
            nltk.download('punkt')
            self.sentences = nltk.sent_tokenize(self.text)

        # Apply SSML to each sentence
        for index, item in enumerate(self.sentences):
            sentence = self._build_ssml_sentence(item)
            self.sentences[index] = sentence

    def _build_ssml_sentence(self, sentence):
        """Wrap sentence in SSML-compatible markup"""
        s = PySSML()
        s.sentence(sentence)
        return s.ssml(True)

    def _build_ssml_title(self, title):
        """Wrap article title in SSML-compatible markup with pause at the end"""
        s = PySSML()
        s.paragraph(title)
        s.pause('500ms')
        return s.ssml(True)

    def _build_chunks(self):
        """Split sentences into AWS Polly synthesizeable chunks"""
        length = len(self.sentences)
        if not length:
            return
        if length == 1:
            self.chunks = self.sentences
            return

        # Summing multiple sentences into single chunk if they are short enough
        for i in range(length):
            # Create chunk if not exist
            if not len(self.chunks):
                self.chunks.append('')

            sentence = self.sentences[i]
            composite = self.chunks[-1] + sentence
            if len(composite) <= self.MAX_LENGTH:
                self.chunks[-1] = composite
            else:
                self.chunks.append(sentence)

    def _finish_chunks(self):
        """"Amazon SSML requires whole text to be wrapped in root <speak> element"""
        for index, item in enumerate(self.chunks):
            chunk = "<speak>%s</speak>" % item
            self.chunks[index] = chunk

    def generate_hash(self):
        """Generate MD5 hash, used for directory naming"""
        m = hashlib.md5()
        m.update(self.text.encode('utf-8'))
        return m.hexdigest()


class AudioRenderer:
    """Representation of single audio chunk rendered via Amazon Polly"""

    def __init__(self, text, filename, fmt='mp3', voice='Brian'):
        self.default_region = 'eu-west-1'
        self.default_url = 'https://polly.eu-west-1.amazonaws.com'
        self.text = text
        self.format = fmt
        self.voice = voice
        self.file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp', filename))

        self.client = self._connect(self.default_region, self.default_url)

    def render(self):
        resp = self.client.synthesize_speech(
            OutputFormat=self.format,
            Text=self.text,
            VoiceId=self.voice,
            TextType='ssml',
            # SpeechMarkTypes=['sentence', 'ssml']
        )

        soundfile = open(self.file_path, 'wb')
        sound_bytes = resp['AudioStream'].read()
        soundfile.write(sound_bytes)
        soundfile.close()

    def clean_up(self):
        os.remove(self.file_path)

    def _connect(self, region_name, endpoint_uri):
        return boto3.client(
            'polly',
            region_name=region_name,
            endpoint_url=endpoint_uri,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )


class Podcast(object):
    # Podcast attributes
    id = None
    title = None
    author = None
    link = None
    logo = None
    subtitle = '-'
    language = 'en'

    def __init__(self, slug, items=[]):
        self.slug = slug
        self.items = items

    def build(self):
        fg = FeedGenerator()

        fg.id(self.id)
        fg.title(self.title)
        fg.author({'name': self.author, 'email': 'john@example.com'})
        fg.link(href=self.link, rel='alternate')
        fg.logo(self.logo)
        fg.subtitle(self.subtitle)
        fg.language(self.language)

        fg.load_extension('podcast', rss=True)
        fg.podcast.itunes_category('Technology', 'Podcasting')

        for item in self.items:
            fe = fg.add_entry()
            fe.id(item['id'])
            fe.title(item['title'])
            # fe.description(item['description'])
            fe.description('Enjoy our first episode.')
            fe.enclosure(
                os.path.basename(item['file']),
                str(os.path.getsize(item['file'])).encode("utf-8").decode("utf-8"),
                'audio/mpeg',
            )

        self.body = fg.rss_str(pretty=True).decode("utf-8")

    def __save_path(self):
        filename = "%s.xml" % self.slug
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp', filename))

    def write(self):
        text_file = open(self.__save_path(), "w")
        text_file.write(self.body)
        text_file.close()


def build():
    # url = "https://feeds.feedburner.com/CoinDesk"
    url = "https://themerkle.com/feed/"
    feed = feeds.Feed(url)
    feed.parse()

    txt = AudioArticle(text=feed.items[-1].description.text, title=feed.items[-1].title)
    txt.render()
    print(txt.audiofile)

    slug = 'themerkle'

    # TODO: Implement podcast item class
    items = [{
        'id': feed.items[-1].id,
        'title': feed.items[-1].title,
        'description': feed.items[-1].description.text,
        'file': txt.audiofile,
    }]
    podcast = Podcast(slug, items)
    podcast.title = feed.title
    podcast.link = feed.link
    podcast.author = 'John Doe'

    podcast.build()
    podcast.write()


build()
