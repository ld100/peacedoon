#!/usr/bin/env python
# -*- coding: utf-8 -*-

import podcasts

url = "https://themerkle.com/feed/"
slug = "themerkle"
pb = podcasts.PodcastBuilder(url, slug)
location = pb.build()
print(location)
