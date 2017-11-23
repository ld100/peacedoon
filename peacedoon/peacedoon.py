#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import boto3
import nltk

import settings
import feeds


class AudioText:
    def __init__(self, text=None, voice='Matthew', language='english'):
        # AWS max length
        self.MAX_LENGTH = 1500

        self.text = text
        self.language = language
        self.voice = voice

        self.sentences = []
        self._build_sentences()

        # We render chunks of text, which are under 1500 chars
        # Due to AWS Polly limitation
        self.chunks = []
        self._build_chunks()

    # TODO: Glue chunks
    # TODO: Add background noise and music
    # TODO: Create unique filenames for chunks
    def render(self):
        for i, e in zip(range(len(self.chunks)), self.chunks):
            filename = "%i.mp3" % i
            chunk = self._render_chunk(e, filename)
            # chunk.clean_up()

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


class AudioRenderer:
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
            VoiceId=self.voice
        )

        soundfile = open(self.file_path, 'wb')
        soundBytes = resp['AudioStream'].read()
        soundfile.write(soundBytes)
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


# def build():
#     url = "https://feeds.feedburner.com/CoinDesk"
#     feed = feeds.Feed(url)
#     feed.parse()
#     content = feed.items[-1].title + ".\n" + feed.items[-1].description.text
#     # content = feed.items[-1].title
#     txt = AudioText(content)
#     print(txt.chunks)
#     txt.render()
#
#
# build()
