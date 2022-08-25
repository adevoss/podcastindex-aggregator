#!/usr/bin/env python3

import sys
import os
import json
import tempfile
import requests

import xml.etree.cElementTree as ET

import PIfunctions
import configuration
import generalfunctions

def search_podcast(query, log_path):
    feeds = []
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl  + 'search/byterm?q=' + query + "&pretty"
    result = PIfunctions.request(url, log_path)

    count = result['count']
    if count > 0:
        for feed in result['feeds']:
            feeds.append(feed)
    else:
        print('No match')

    for feed in feeds:
        print(feed['title'] + ' ' + str(feed['id']))
    return feeds

def livestream(feed_url, feed_id, feed_title, playlist_path, log_path):
    try:
       tzpretty = "Europe/Amsterdam"
       now = generalfunctions.now()
       nowTZ = generalfunctions.date_to_tz(now, tzpretty)
       nowseconds = generalfunctions.to_epoch(nowTZ)
       nowstring = generalfunctions.format_dateYYYMMDDHHMM(nowTZ)
       formatpretty = "%H:%M %m/%d/%Y"
       tomorrowTZ = generalfunctions.tomorrow()
       message = feed_url + ' not live now'

       PIurl = configuration.config["podcastindex"]["url"]
       url = PIurl  + "episodes/live/byfeedid?id=" + str(feed_id) + "&pretty"
       url = PIurl  + "episodes/live"
       lits = None
       #lits = PIfunctions.request(url, log_path)
       if lits != None:
          status = generalfunctions.to_boolean(lits['status'])
          if status:
             lits = lits['items']
             for lit in lits:
                 if lit['feedId'] == feed_id:
                    message = 'TESTING'
                    #message = lit['title'] + ' at ' + startdatepretty  + ' on ' + url
                    generalfunctions.log(log_path, message, False, False)
                    print(message)

       xml = loadXML_podcast(feed_url)
       lits = get_liveitems(xml)
       if lits != None and len(lits) > 0:
          for lit in lits:
              message = feed_url + ' not live now'
              onair = False
              status = get_liveitem_status(lit)
              start = get_liveitem_start(lit)
              end = get_liveitem_end(lit)
              title = get_liveitem_title(lit)
              url = get_liveitem_url(lit)

              status = status.lower()
              if title == "":
                 title = feed_title
              if url == "":
                 url = "<not set>"

              if start != "":
                 startdate = generalfunctions.string_to_date(start)
                 startdateTZ = generalfunctions.date_to_tz(startdate, tzpretty)
                 startdatestring = generalfunctions.format_dateYYYMMDDHHMM(startdateTZ)
                 startdatepretty = startdateTZ.strftime(formatpretty)
                 startdateseconds = generalfunctions.to_epoch(startdateTZ)

                 live_announce_hours = int(configuration.config["settings"]["announceLive"])
                 live_announce_seconds = live_announce_hours * 3600
                 announceseconds = nowseconds + live_announce_seconds
                 announcedate = generalfunctions.to_date(announceseconds)
                 announcedateTZ = generalfunctions.date_to_tz(announcedate, tzpretty)

                 live_leadin = -int(configuration.config["settings"]["leadinLive"])
                 live_leadout = int(configuration.config["settings"]["leadoutLive"])

              if end != "":
                 enddate = generalfunctions.string_to_date(end)
                 enddateTZ = generalfunctions.date_to_tz(enddate, tzpretty)
                 enddatestring = generalfunctions.format_dateYYYMMDDHHMM(enddateTZ)
                 enddatepretty = str(enddateTZ)
                 enddatepretty = enddateTZ.strftime(formatpretty)

              if startdatestring != "":
                 if startdateTZ > nowTZ and startdateTZ <= announcedateTZ:
                    message = title + ' at ' + startdatepretty  + ' on ' + url
                    if startdateTZ.date() == nowTZ.date():
                       message = title + ' today at ' + str(startdateTZ.time()) + ' on ' + url
                    if startdateTZ.date() == tomorrowTZ.date():
                       message = title + ' tomorrow at ' + str(startdateTZ.time()) + ' on ' + url
                    onair = True
                 if enddatestring != "":
                    leadindateTZ = generalfunctions.deltaminutes(startdateTZ, live_leadin)
                    leadoutdateTZ = generalfunctions.deltaminutes(enddateTZ, live_leadout)
                    if status == "live" and (leadindateTZ <= nowTZ and leadoutdateTZ >= nowTZ):
                       message = title + ' NOW on ' + url
                       onair = True

              if onair:
                 generalfunctions.writetext(playlist_path, message)
                 print(message)

    except Exception as e:
        message = str(e)
        generalfunctions.log(log_path, message, True, False)
        print(message)

def loadXML_podcast(feed):
    root = None
    response = requests.get(feed)
    fd, path = tempfile.mkstemp()
    try:
       with os.fdopen(fd, 'wb') as tmp:
          tmp.write(response.content)
       tree = ET.parse(path)
       root = tree.getroot()
    finally:
       os.remove(path)
    return root

def get_liveitems(root):
    podcast = {'podcast': 'https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md'}
    lits = None
    if root != "" and root != None:
       channel = root.find('channel')
       if channel != "" and channel != None:
          lits = channel.findall('podcast:liveItem', podcast)
    return lits

def get_liveitem_status(lit):
    status = ""
    if lit != "":
       status = lit.attrib.get('status')
    return status

def get_liveitem_start(lit):
    start = ""
    if lit != "":
       start = lit.attrib.get('start')
    return start

def get_liveitem_end(lit):
    end = ""
    if lit != "":
       end = lit.attrib.get('end')
    return end

def get_liveitem_title(lit):
    title = ""
    if lit != "":
       if lit.find('title') != None:
          title = lit.find('title').text
    return title

def get_liveitem_url(lit):
    url = ""
    if lit != "":
       url = lit.find('enclosure').attrib.get('url')
    return url

def search_podcast_by_feed(feed, log_path):
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl + "podcasts/byfeedurl?url=" + feed + "&pretty"
    #generalfunctions.log(log_path, url, False, True)
    search_result = PIfunctions.request(url, log_path)
    status = generalfunctions.to_boolean(search_result['status'])
    if status:
       podcast_id = search_result['feed']['id']
    else:
       podcast_id = ""
    return podcast_id

def search_podcast_by_id(feedId, log_path):
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl + "podcasts/byfeedid?id=" + feedId + "&pretty"
    #generalfunctions.log(log_path, url, False, True)
    search_result = PIfunctions.request(url, log_path)
    status = generalfunctions.to_boolean(search_result['status'])
    if status:
       feed_url = search_result['feed']['url']
    else:
       feed_url = ""
    return feed_url

def podcastdata(feedId, log_path):
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl  + "podcasts/byfeedid?id=" + str(feedId)
    #generalfunctions.log(log_path, url, False, True)
    feed_result = PIfunctions.request(url, log_path)
    return feed_result

def check_podcast_feed(title, feedId, feedurl, playlist_path, log_path, verbose):
    current = False
    feedurlPI = search_podcast_by_id(feedId, log_path)
    if feedurl == feedurlPI:
       current = True
       message = 'Checking feed url of ' + title + ' - ' + feedurl
    else:
       message = title + ' - feed url has changed from ' + feedurl + ' to ' + feedurlPI + ' *** Please edit podcast list'

    if not current:
       generalfunctions.log(log_path, message, False, False)

    if verbose:
       generalfunctions.writetext(playlist_path, message)
       print(message)

def episodes(feedId, number_of_episodes, log_path):
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl + "episodes/byfeedid?id=" + str(feedId) + "&max=" + str(number_of_episodes)
    #generalfunctions.log(log_path, url, False, True)
    episodes_result = PIfunctions.request(url, log_path)
    return episodes_result

def process_file(data, data_path, number_of_episodes, log_path, playlist_path, playlist_client_path, overwrite, mode, podcast_to_process):
    for podcast_data in data['podcastlist']:
        feedurl = "-"
        verbose = False
        if mode == "CHECK":
           verbose = True

        if podcast_data["id"][:1] != '#':
           if podcast_to_process == "ALL" or str(podcast_to_process) == podcast_data["id"] or str(podcast_to_process) == podcast_data["feed"]:
              if mode == "LIST":
                 print(podcast_data['title'] + ' ' + podcast_data['id'])

              if mode == "CHECK" or mode == "PROCESS":
                 check_podcast_feed(podcast_data['title'], podcast_data['id'], podcast_data['feed'], playlist_path, log_path, verbose)

              if mode == "LIVE":
                 livestream(podcast_data['feed'], podcast_data['id'], podcast_data['title'], playlist_path, log_path)

              if mode == "PROCESS":
                 process_podcast(podcast_data, number_of_episodes, data_path, log_path, playlist_path, playlist_client_path, overwrite, mode)
        else:
           if podcast_to_process == "ALL":
              message = 'Skipping podcast \'' + podcast_data["title"] + '\''
              generalfunctions.log(log_path, message, False, False)

def process_podcast(podcast_data, number_of_episodes, data_path, log_path, playlist_path, playlist_client_path, overwrite, mode):
    try:
        # create directory for podcast
        podcast_path = os.path.join(data_path, podcast_data["directory"], podcast_data["title"])
        podcast_client_path = os.path.join(playlist_client_path, podcast_data["directory"], podcast_data["title"])
        generalfunctions.create_directory(podcast_path)

        # logging
        message = 'Processing podcast \'' + podcast_data["title"] + '\''
        print('==========================================================')
        print(message)
        print('==========================================================')
        generalfunctions.log(log_path, message, False, False)

        feed = podcastdata(podcast_data["id"], log_path)["feed"]

        # livestream
        if mode == "PROCESS" or mode == "LIVE":
           livestream(feed["url"], feed["id"], feed["title"], playlist_path, log_path)

        if mode == "PROCESS":
           # download feed assets
           path = 'data.json'
           path = os.path.join(podcast_path, path)
           generalfunctions.write_file(path, json.dumps(feed, indent = 2))

           # image
           url = feed["image"]
           path = os.path.basename(url)
           path = os.path.join(podcast_path, path)
           path = path.split('?')[0]
           downloaded = generalfunctions.download(url, path, log_path, overwrite)

           # process episodes
           process_episodes(podcast_data["id"], number_of_episodes, podcast_data["title"], podcast_path, log_path, playlist_path, podcast_client_path, overwrite)

    except Exception as e:
        message = e
        generalfunctions.log(log_path, message, True, False)
        print(message)

def process_chapter(chapter, path, log_path, overwrite):
    # logging
    chapter_title = str(chapter["title"][0:50])
    message = 'Processing chapter \'' + chapter_title + '\''
    print(message)
    generalfunctions.log(log_path, message, False, False)

    # create directory for chapter
    chapter_directory = str(chapter["startTime"]) + '-' + chapter_title
    path = os.path.join(path, chapter_directory)
    generalfunctions.create_directory(path)
    chapter_path = path

    # write json data
    path = 'data.json'
    path = os.path.join(chapter_path, path)
    generalfunctions.write_file(path, json.dumps(chapter, indent = 2))

    # image
    if "img" in chapter:
        url = chapter["img"]
        path = os.path.basename(url)
        file_name = generalfunctions.file_name_noextension(path)
        file_extension = generalfunctions.file_extension(path)
        #file_extention = file_extention.lower()
        if file_extension == '.png' or file_extension == '.jpg' or file_extension == '.jpeg':
            path = os.path.join(chapter_path, path)
            generalfunctions.download(url, path, log_path, overwrite)

    # url
    if "url" in chapter:
        url = chapter["url"]
        path = os.path.basename(url)
        file_name = generalfunctions.file_name_noextension(path)
        file_extension = generalfunctions.file_extension(path)
        #file_extention = file_extention.lower()
        if file_extension == '.pdf' or file_extension == '.png' or file_extension == '.jpg' or file_extension == '.docx':
            path = os.path.join(chapter_path, path)
            # don't overwrite files
            if os.path.isfile(path):
                now = generalfunctions.now()
                dateFormatted = generalfunctions.format_dateYYYMMDDHHMM(now)
                path = os.path.join(chapter_path, file_name+'-'+dateFormatted+file_extension)

            path = os.path.join(chapter_path, path)
            generalfunctions.download(url, path, log_path, overwrite)


def process_episode(episode, path, overwrite, log_path, playlist_path, podcast_client_path):
    title = episode["title"]

    # logging
    message = 'Processing episode \'' + title + '\''
    print('==========================================================')
    print(message)
    print('==========================================================')
    generalfunctions.log(log_path, message, False, False)

    # create directory for episode
    episode_path = os.path.join(path, title)
    episode_client_path = os.path.join(podcast_client_path, title)
    generalfunctions.create_directory(episode_path)

    path = 'data.json'
    path = os.path.join(episode_path, path)
    generalfunctions.write_file(path, json.dumps(episode, indent = 2))

    # download episode assets

    # image
    url = episode["image"]
    if url != None and url != '':
        path = os.path.basename(url)
        path = path.split('?')[0]
        path = os.path.join(episode_path, path)
        generalfunctions.download(url, path, log_path, overwrite)

    # enclosure url
    url = episode["enclosureUrl"]
    if url != None and url != '':
        url = episode["enclosureUrl"]
        enclosure_file = os.path.basename(url)
        enclosure_file = enclosure_file.split('?')[0]
        enclosure_path = os.path.join(episode_path, enclosure_file)
        enclosure_client_path = os.path.join(episode_client_path, enclosure_file)
        downloaded = generalfunctions.download(url, enclosure_path, log_path, overwrite)
        if downloaded:
           generalfunctions.writetext(playlist_path, enclosure_client_path)

    # chapters
    url = episode["chaptersUrl"]
    if url != None and url != '':
        path = os.path.basename(url)
        path = os.path.join(episode_path, path)
        downloaded = generalfunctions.download(url, path, log_path, True)
        if downloaded:
           chapter_file = path

           # create directory for chapters
           path = os.path.join(episode_path, 'Chapters')
           generalfunctions.create_directory(path)
           chapter_path = path

           # download chapters
           chapters = generalfunctions.read_json(chapter_file, log_path)
           if chapters != None and chapters != '':
              for (chapter) in chapters["chapters"]:
                  process_chapter(chapter, chapter_path, log_path, overwrite)

    # transcript
    url = episode["transcriptUrl"]
    if url != None and url != '':
        path = os.path.basename(url)
        path = os.path.join(episode_path, path)
        generalfunctions.download(url, path, log_path, True)

def process_episodes(feedId, number_of_episodes, feedTitle, path, log_path, playlist_path, podcast_client_path, overwrite):
    # create directory for episodes
    path = os.path.join(path, 'Episodes')
    podcast_client_path = os.path.join(podcast_client_path, 'Episodes')
    generalfunctions.create_directory(path)

    episodes_data = episodes(feedId, number_of_episodes, log_path)["items"]
    # print(json.dumps(episodes_data, indent = 2))
    for (episode) in episodes_data:
        process_episode(episode, path, overwrite, log_path, playlist_path, podcast_client_path)

def aggregate(mode, podcast_to_process, number_of_episodes):
    try:
        datadir = configuration.config["directory"]["data"]
        playlist_client_path = configuration.config["directory"]["playlist"]
        podcastlist_file = configuration.config["file"]["podcastlist"]

        # create directory
        log_path = os.path.join(datadir, configuration.config["directory"]["log"])
        generalfunctions.create_directory(log_path)
        playlist_path = os.path.join(datadir, configuration.config["directory"]["play"])
        generalfunctions.create_directory(playlist_path)

        now = generalfunctions.now()
        if podcast_to_process == "ALL":
           dateString = generalfunctions.format_dateYYYMMDDHHMM(now)
        else:
           dateString = generalfunctions.format_dateYYYMMDDHHMMSS(now)

        log_path = os.path.join(log_path, dateString+'.log')
        playlist_path = os.path.join(playlist_path, dateString+'.m3u')
        overwrite = False

        # logging
        if podcast_to_process == "ALL":
           message = 'Processing file \''+ podcastlist_file + '\''
           generalfunctions.log(log_path, message, False, False)
        else:
           message = 'Processing podcast \''+ podcast_to_process + '\''

        now = generalfunctions.now()
        data = generalfunctions.read_json(podcastlist_file, log_path)
        if mode == 'SEARCH':
           search_podcast(str(podcast_to_process), log_path)
        else:
           process_file(data, datadir, number_of_episodes, log_path, playlist_path, playlist_client_path, overwrite, mode, podcast_to_process)

    except Exception as e:
        message = e
        print(message)
        generalfunctions.log(log_path, message, True, False)


try:
    mode = "PROCESS"
    podcast_to_process = "ALL"
    number_of_episodes = 0

    if len(sys.argv) == 4:
       mode = sys.argv[1]
       podcast_to_process = sys.argv[2]
       number_of_episodes = sys.argv[3]

    if len(sys.argv) == 3:
       mode = sys.argv[1]
       podcast_to_process = sys.argv[2]

    if len(sys.argv) == 2:
       mode = sys.argv[1]
       podcast_to_process = "ALL"

    if mode == "-h" or mode == "--help":
       print ('Usage: ' + sys.argv[0] + ' [LIST | SEARCH | CHECK | LIVE | PROCESS] [ALL|<search term>|<podcastindex-id>|<feedurl>] [numberOfEpisodes]')
    else:
       configuration.read() 
       if mode == "PROCESS" or mode == "LIST" or mode == "SEARCH" or mode == "CHECK" or mode == "LIVE":
          if int(number_of_episodes) == 0:
             number_of_episodes = int(configuration.config["settings"]["numberOfEpisodes"])

          aggregate(mode, podcast_to_process, number_of_episodes)

except Exception as e:
    message = e
    message = 'Function: ' + function.__name__ + ': ' + str(e)
    generalfunctions.log(log_path, message, True, False)
    print(message)
