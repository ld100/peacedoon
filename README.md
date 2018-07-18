# Peacedoon

Peacedoon is a tool for transforming RSS feeds into full-fledged podcasts.

Peacedoon is an opinionated solution with following workflow:

1. Take RSS/ATOM feed at specified URL and parse it;
2. Transform each feed item into separate MP3 file (using Amazon Polly), mix it with ambient music;
3. Build a podcast RSS XML based on initial feed and newly created MP3 files;
4. Upload MP3 audio and podcast XML to Amazon S3 and provide a podcast link.

Currently Peacedoon works just with English texts, however Russian and Spanish are in the roadmap.