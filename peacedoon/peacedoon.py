#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import boto3
import settings
import feeds

default_region = 'eu-west-1'
default_url = 'https://polly.eu-west-1.amazonaws.com'
TMP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))

def connect(region_name=default_region, endpoint_uri=default_url):
    return boto3.client(
        'polly',
        region_name=region_name,
        endpoint_url=endpoint_uri,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def speak(polly, text, format='mp3', voice='Brian'):
    resp = polly.synthesize_speech(OutputFormat=format, Text=text, VoiceId=voice)
    FILE_PATH = os.path.join(TMP_PATH, 'sound.mp3')

    soundfile = open(FILE_PATH, 'wb')
    soundBytes = resp['AudioStream'].read()
    soundfile.write(soundBytes)
    soundfile.close()
    # os.system('afplay /tmp/sound.mp3')  # Works only on Mac OS, sorry
    # os.remove(FILE_PATH)


polly = connect()
# speak(polly, "Hello world, I'm Polly. Or Brian. Or anyone you want, really.", voice='Matthew')
URL = "http://feeds.feedburner.com/PythonInsider"
feed = feeds.Feed(URL)
feed.parse()
# content = feed.items[-1].title + "\n" + feed.items[-1].description_text
content = feed.items[-1].title
speak(polly, content, voice='Matthew')
