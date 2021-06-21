# podcastindex-aggregator
Download your podcasts using the Podcast Index (https://podcastindex.org)

To use you need a key. Please go to https://api.podcastindex.org/signup

Example:
/path/to/aggregator.py

Options:
/path/to/aggregator.py [ALL|PodcastIndex id]
No options is the same as ALL

configuration.json:
- podcastindex: use your key and secret

- data: Directory where the podcasts are stored
- log: Subdirectory of 'data' where log files are stored
- play: Subdirectory of 'data' where playlist files are stored
- playlist: Path to 'data' on the computer used to play the podcasts

- podcastlist: path to the podcastlist.json file

podcastlist.json:
- id: search for the id on https://podcastindex.org. The id is at the end of the url.
- title: Used only for the file to be readable.
- directory: Subdirectory of 'data' (see above) to store the podcast in.

