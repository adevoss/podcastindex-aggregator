# podcastindex-aggregator
Download your podcasts using the Podcast Index (https://podcastindex.org)

Prerequisites:
- To use you need a key. Please go to https://api.podcastindex.org/signup
- Install 'wget' using the package manager
- Create a Python virtual environment

Example:
python3 /path/to/aggregator.py

Options:
/path/to/aggregator.py [LIST | CHECK | LIVE | PROCESS] [ALL|<podcastindex-id>|<feedurl>] [numberOfEpisodes] [verbosity 0|1]
No options is the same as PROCESS ALL

LIST - Show list of podcasts in your podcastlist
SEARCH - Search podcasts
CHECK - Compares feed url in config file to feed url in podcastindex
LIVE - Generates a playlist file for live podcasts
PROCESS - Download podcasts

configuration.json:
- podcastindex: use your key and secret
- wait: pause between calls to the podcastindex
- enable: use querystring tracking or not
- enable: use podtrac tracking or not
- enable: use op3 tracking or not
- data: Directory where the podcasts are stored
- log: Subdirectory of 'data' where log files are stored
- play: Subdirectory of 'data' where playlist files are stored
- playlist: Path to 'data' on the computer used to play the podcasts
- podcastlist: path to the podcastlist.json file
- numberOfEpisodes: maximum number of episodes to download
- announceLive: a live show will only be shown in the playlist this number of hours before the start of the live show
- leadinLive: a live show will only be shown in the playlist as live NOW when status is 'live' and the current time is this amount of minutes before 'start'
- leadoutLive: a live show will only be shown in the playlist as live NOW when status is 'live' and the current time is this amount of minutes after 'end'
- timeoutConnect: seconds for connecting to server
- timeoutRead: seconds for timeout while downloading

podcastlist.json:
- id: search for the id on https://podcastindex.org. The id is at the end of the url.
- title: Used for creating directory.
- feed: feed of podcast to avoid api call with hivewatcher
- live: Indicates if feed is a feed with liveItem tags [0|1]. Creates a separate playlist.
- directory: Subdirectory of 'data' (see above) to store the podcast in.

