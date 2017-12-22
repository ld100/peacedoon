#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib

import boto3
import nltk
from pyssml.PySSML import PySSML
from pydub import AudioSegment

import settings
import feeds


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

    # TODO: Glue chunks
    # TODO: Add background noise and music
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


def build():
    # url = "https://feeds.feedburner.com/CoinDesk"
    url = "https://themerkle.com/feed/"
    feed = feeds.Feed(url)
    feed.parse()

    txt = AudioArticle(text=feed.items[-1].description.text, title=feed.items[-1].title)
    # print(txt.generate_hash())
    # print(txt.chunks)
    txt.render()
    print(txt.audiofile)

build()
