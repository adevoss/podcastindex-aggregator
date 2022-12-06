#!/usr/bin/env python3

import sys
import os
import json
import tempfile
import requests

import xml.etree.cElementTree as ET

import config
import log
import PIfunctions
import generalfunctions


def download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead):
    downloaded = 100

    try:
      file_name = os.path.basename(path)
      file_extention = os.path.splitext(file_name)[1]

      if file_extention == '.mp3':
         downloaded = generalfunctions.download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead, True, True, True)

    except Exception as e:
       message = str('wget')
       log.log(True, 'WARN', message)
       message = str(e)
       log.log(True, 'WARN', message)
       message = str(url)
       log.log(True, 'WARN', message)

    try:
       if downloaded >= 10:
          if file_extention == '.mp3':
             downloaded = generalfunctions.download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead, False, False, True)
          else:
             downloaded = generalfunctions.download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead, False, False, False)

    except Exception as e:
       message = str('request')
       log.log(True, 'ERROR', message)
       message = str(e)
       log.log(True, 'ERROR', message)
       print(message)
       message = str(url)
       log.log(True, 'ERROR', message)
       print(message)

    return downloaded

def strip_tracking(url):
    chtbl = bool(config.file["chtbl"]["enable"])
    chtblurl  = str(config.file["chtbl"]["url"])

    chrt = bool(config.file["chrt"]["enable"])
    chrturl  = str(config.file["chrt"]["url"])

    pdcn = bool(config.file["pdcn"]["enable"])
    pdcnurl  = str(config.file["pdcn"]["url"])

    podtrac = bool(config.file["podtrac"]["enable"])
    podtracurl = str(config.file["podtrac"]["url"])

    op3 = bool(config.file["op3"]["enable"])
    op3url = str(config.file["op3"]["url"])

    i = 1
    while i <= 2:
       if not chtbl:
          url = url.replace(chtblurl, 'https://')
       if not chrt:
          url = url.replace(chrturl, 'https://')
       if not pdcn:
          url = url.replace(pdcnurl, 'https://')
       if not podtrac:
          url = url.replace(podtracurl, 'https://')
       if not op3:
          url = url.replace(op3url, 'https://')
       i += 1

    return url

def pi_search_podcast(query):
    feeds = []
    PIurl = config.file["podcastindex"]["url"]
    url = PIurl  + 'search/byterm?q=' + query + "&pretty"
    result = PIfunctions.request(url)

    if result == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    else:
       count = result['count']
       if count > 0:
           for feed in result['feeds']:
               feeds.append(feed)
       else:
           print('No match')

       for feed in feeds:
           print(feed['title'])
           print('Podcasting 2.0 id: ' + str(feed['id']))
           print(feed['url'])
    return feeds

def livestream(feed_url, feed_id, feed_title, playlist_path):
    try:
       tzpretty = "Europe/Amsterdam"
       now = generalfunctions.now()
       nowTZ = generalfunctions.date_to_tz(now, tzpretty)
       nowseconds = generalfunctions.to_epoch(nowTZ)
       nowstring = generalfunctions.format_dateYYYMMDDHHMM(nowTZ)
       formatpretty = "%H:%M %m/%d/%Y"
       tomorrowTZ = generalfunctions.tomorrow()
       message = feed_url + ' not live now'

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

                 live_announce_hours = int(config.file["settings"]["announceLive"])
                 live_announce_seconds = live_announce_hours * 3600
                 announceseconds = nowseconds + live_announce_seconds
                 announcedate = generalfunctions.to_date(announceseconds)
                 announcedateTZ = generalfunctions.date_to_tz(announcedate, tzpretty)

                 live_leadin = -int(config.file["settings"]["leadinLive"])
                 live_leadout = int(config.file["settings"]["leadoutLive"])

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
        log.log(True, 'ERROR', message)
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
    url = None
    if lit != None and lit != '':
       url = lit.find('enclosure').attrib.get('url')
       if url != None and url != '':
          url = strip_tracking(url)
    return url

def pi_search_podcast_by_feed(feed):
    PIurl = config.file["podcastindex"]["url"]
    url = PIurl + "podcasts/byfeedurl?url=" + feed + "&pretty"
    search_result = PIfunctions.request(url)
    if search_result == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    else:
       status = generalfunctions.to_boolean(search_result['status'])
       if status:
          podcast_id = search_result['feed']['id']
       else:
          podcast_id = ""
    return podcast_id

def pi_search_podcast_by_id(feedId):
    feed_url = None
    PIurl = config.file["podcastindex"]["url"]
    url = PIurl + "podcasts/byfeedid?id=" + feedId + "&pretty"
    search_result = PIfunctions.request(url)
    if search_result == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    else:
       status = generalfunctions.to_boolean(search_result['status'])
       if status:
          feed_url = search_result['feed']['url']
    return feed_url

def pi_podcastdata(feedId):
    feed_result = None
    PIurl = config.file["podcastindex"]["url"]
    url = PIurl  + "podcasts/byfeedid?id=" + str(feedId)
    feed_result = PIfunctions.request(url)
    if feed_result == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    return feed_result

def check_podcast_feed(title, feedId, feedurl, playlist_path, verbose):
    current = False
    feedurlPI = pi_search_podcast_by_id(feedId)
    if feedurlPI == None:
       message = 'Podcasts can\'t be checked.'
       log.log(True, 'ERROR', message)
       print(message)
    else:
       if feedurl == feedurlPI:
          current = True
          message = 'Checking feed url of ' + title + ' - ' + feedurl
       else:
          message = title + ' - feed url has changed from ' + feedurl + ' to ' + feedurlPI + ' *** Please edit podcast list'

    if not current:
       log.log(False, 'INFO', message)
       print(message)

    if verbose:
       generalfunctions.writetext(playlist_path, message)
       print(message)

def pi_episodes(feedId, number_of_episodes):
    PIurl = config.file["podcastindex"]["url"]
    url = PIurl + "episodes/byfeedid?id=" + str(feedId) + "&max=" + str(number_of_episodes)
    episodes_result = PIfunctions.request(url)
    if episodes_result == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    return episodes_result

def process_file(data, data_path, number_of_episodes, playlist_path, playlist_client_path, overwrite, mode, podcast_to_process):
    for podcast_data in data['podcastlist']:
        feedurl = "-"
        verbose = False
        if mode == "CHECK":
           verbose = True

        if podcast_data["id"][:1] != '#':
           if podcast_to_process == "ALL" or str(podcast_to_process) == podcast_data["id"] or str(podcast_to_process) == podcast_data["title"] or str(podcast_to_process) == podcast_data["feed"]:

              # logging
              message = 'Processing podcast \'' + podcast_data["title"] + '\''
              print('==========================================================')
              print(message)
              print('==========================================================')
              log.log(False, 'INFO', message)

              if mode == "LIST":
                 print(podcast_data['title'] + ' ' + podcast_data['id'])

              if mode == "CHECK" or mode == "PROCESS":
                 check_podcast_feed(podcast_data['title'], podcast_data['id'], podcast_data['feed'], playlist_path, verbose)

              if mode == "LIVE" or mode == "PROCESS":
                 livestream(podcast_data['feed'], podcast_data['id'], podcast_data['title'], playlist_path)

              if mode == "PROCESS":
                 process_podcast(podcast_data, number_of_episodes, data_path, playlist_path, playlist_client_path, overwrite, mode)
        else:
           if podcast_to_process == "ALL":
              message = 'Skipping podcast \'' + podcast_data["title"] + '\''
              log.log(False, 'INFO', message)

def process_podcast(podcast_data, number_of_episodes, data_path, playlist_path, playlist_client_path, overwrite, mode):
    try:
        # create directory for podcast
        podcast_path = os.path.join(data_path, podcast_data["directory"], podcast_data["title"])
        podcast_client_path = os.path.join(playlist_client_path, podcast_data["directory"], podcast_data["title"])
        generalfunctions.create_directory(podcast_path)

        feed = pi_podcastdata(podcast_data["id"])

        if feed != None:
           feed = feed["feed"]

           if mode == "PROCESS":
              # download feed assets
              path = 'data.json'
              path = os.path.join(podcast_path, path)
              generalfunctions.write_file(path, json.dumps(feed, indent = 2))

              # image
              url = feed["image"]
              if url != None and url != '':
                 path = os.path.basename(url)
                 path = os.path.join(podcast_path, path)
                 path = path.split('?')[0]
                 querystringtracking = bool(config.file["querystringtracking"]["enable"])
                 downloaded = download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead)
                 if downloaded >= 10:
                    config.exception_count += 1
                    message = 'Podcast image (' + url + ') not downloaded. Returncode: ' + str(downloaded)
                    log.log(True, 'ERROR', message)

              # process episodes
              process_episodes(podcast_data["id"], number_of_episodes, podcast_data["title"], podcast_path, playlist_path, podcast_client_path, overwrite)

    except Exception as e:
        message = e
        print(message)

def process_chapter(chapter, path, overwrite):
    # logging
    chapter_title = str(chapter["title"][0:50])
    message = 'Processing chapter \'' + chapter_title + '\''
    print(message)
    log.log(False, 'INFO', message)

    # create directory for chapter
    chapter_title = generalfunctions.sanitize_path(chapter_title, False)
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
            querystringtracking = bool(config.file["querystringtracking"]["enable"])
            generalfunctions.download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead)

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
            querystringtracking = bool(config.file["querystringtracking"]["enable"])
            generalfunctions.download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead)


def process_episode(episode, path, overwrite, playlist_path, podcast_client_path):
    title = episode["title"]
    title = generalfunctions.sanitize_path(title, False)

    # logging
    message = 'Processing episode \'' + title + '\''
    print('==========================================================')
    print(message)
    print('==========================================================')
    log.log(False, 'INFO', message)

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
        querystringtracking = bool(config.file["querystringtracking"]["enable"])
        generalfunctions.download(url, path, overwrite, querystringtracking, timeoutConnect, timeoutRead)

    # enclosure url
    url = episode["enclosureUrl"]
    if url != None and url != '':
       url = episode["enclosureUrl"]

       url = strip_tracking(url)

       enclosure_file = os.path.basename(url)
       enclosure_file = enclosure_file.split('?')[0]
       enclosure_path = os.path.join(episode_path, enclosure_file)
       enclosure_client_path = os.path.join(episode_client_path, enclosure_file)
       querystringtracking = bool(config.file["querystringtracking"]["enable"])

       downloaded = download(url, enclosure_path, overwrite, querystringtracking, timeoutConnect, timeoutRead)
       if downloaded == 0:
          config.count_newpodcasts += 1
          generalfunctions.writetext(playlist_path, enclosure_client_path)
       if downloaded >= 10:
          config.exception_count += 1
          message = 'Podcast not downloaded. Returncode: ' + str(downloaded)
          log.log(True, 'ERROR', message)

    # chapters
    url = episode["chaptersUrl"]
    if url != None and url != '':
        path = os.path.basename(url)
        path = os.path.join(episode_path, path)
        querystringtracking = bool(config.file["querystringtracking"]["enable"])
        downloaded = download(url, path, True, querystringtracking, timeoutConnect, timeoutRead)
        if downloaded == 0:
           chapter_file = path

           # create directory for chapters
           path = os.path.join(episode_path, 'Chapters')
           generalfunctions.create_directory(path)
           chapter_path = path

           # download chapters
           chapters = generalfunctions.read_json(chapter_file)
           if chapters != None and chapters != '':
              for (chapter) in chapters["chapters"]:
                  process_chapter(chapter, chapter_path, overwrite)
        else: 
           config.exception_count += 1
           message = 'Podcast chapters not downloaded. Returncode: ' + str(downloaded)
           log.log(True, 'ERROR', message)

    # transcript
    url = episode["transcriptUrl"]
    if url != None and url != '':
        path = os.path.basename(url)
        path = os.path.join(episode_path, path)
        querystringtracking = bool(config.file["querystringtracking"]["enable"])
        generalfunctions.download(url, path, True, querystringtracking, timeoutConnect, timeoutRead)

def process_episodes(feedId, number_of_episodes, feedTitle, path, playlist_path, podcast_client_path, overwrite):
    # create directory for episodes
    path = os.path.join(path, 'Episodes')
    podcast_client_path = os.path.join(podcast_client_path, 'Episodes')
    generalfunctions.create_directory(path)

    episodes_data = pi_episodes(feedId, number_of_episodes)
    if episodes_data == None:
       config.exception_count += 1
       message = 'Podcast episodes can\'t be downloaded.'
       log.log(True, 'ERROR', message)
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
    else:
       episodes_data = episodes_data["items"]
       for episode in episodes_data:
           process_episode(episode, path, overwrite, playlist_path, podcast_client_path)

def aggregate(mode, podcast_to_process, number_of_episodes):
    try:
        config.exception_count = 0
        config.count_newpodcasts = 0
        datadir = config.file["directory"]["data"]
        playlist_client_path = config.file["directory"]["playlist"]
        podcastlist_file = config.file["file"]["podcastlist"]

        # create directory
        config.log_path = os.path.join(datadir, config.file["directory"]["log"])
        generalfunctions.create_directory(config.log_path)
        playlist_path = os.path.join(datadir, config.file["directory"]["play"])
        generalfunctions.create_directory(playlist_path)

        now = generalfunctions.now()
        if podcast_to_process == "ALL":
           dateString = generalfunctions.format_dateYYYMMDDHHMM(now)
        else:
           dateString = generalfunctions.format_dateYYYMMDDHHMMSS(now)

        config.log_error_path = os.path.join(config.log_path, dateString + '-error.log')
        config.log_path = os.path.join(config.log_path, dateString+'.log')
        log.configure(config.log_path, config.log_error_path)

        playlist_path = os.path.join(playlist_path, dateString+'.m3u')
        overwrite = False

        # logging
        if podcast_to_process == "ALL":
           message = 'Processing file \''+ podcastlist_file + '\''
           log.log(False, 'INFO', message)
        else:
           message = 'Processing podcast \''+ podcast_to_process + '\''

        now = generalfunctions.now()
        data = generalfunctions.read_json(podcastlist_file)
        if mode == 'SEARCH':
           pi_search_podcast(str(podcast_to_process))
        else:
           process_file(data, datadir, number_of_episodes, playlist_path, playlist_client_path, overwrite, mode, podcast_to_process)


        print('==========================================================')

        if config.count_newpodcasts > 0:
           newpodcasts = generalfunctions.read_file(playlist_path)
           if newpodcasts == None:
              print('File ' + playlist_path + ' does not exists')
           else:
              print(newpodcasts)
           print('==========================================================')

        message = 'Finished: ' + str(config.exception_count) + ' errors.'
        if config.exception_count > 0:
           message += ' See ' + config.log_error_path 
           print(message)
           print('==========================================================')

        if mode == 'PROCESS':
           message = str(config.count_newpodcasts) + ' new podcast'
           if config.count_newpodcasts == 0 or config.count_newpodcasts >= 2:
              message += 's'
           message += '.'
           log.log(False, 'INFO', message)
           print(message)
           print('==========================================================')

    except Exception as e:
        message = e
        print(message)
        log.log(True, 'ERROR', message)


try:
    config.file = config.read_file() 

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
       if mode == "PROCESS" or mode == "LIST" or mode == "SEARCH" or mode == "CHECK" or mode == "LIVE":
          if int(number_of_episodes) == 0:
             number_of_episodes = int(config.file["settings"]["numberOfEpisodes"])

          timeoutConnect = int(config.file["settings"]["timeoutConnect"])
          timeoutRead = int(config.file["settings"]["timeoutRead"])

          aggregate(mode, podcast_to_process, number_of_episodes)

except Exception as e:
    message = 'Function: main: ' + str(e)
    log.log(True, 'ERROR', message)
    print(message)

