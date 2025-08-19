#!/usr/bin/env python3

import sys
import os
import json
import tempfile
import requests

import xml.etree.cElementTree as ET

import configuration as config
import log
import PIfunctions
import generalfunctions


def download_result(downloaded):
    result = 999
    if downloaded == 0 or downloaded == 10 or downloaded == 20 or downloaded == 30:
       result = 0
    if downloaded == 1:
       result = 1
    if downloaded == 2:
       result = 2
    return result

def addto_playlist_m3u(playlist_path, path_name, podcast_title, episode, length, dateString, count, directory_delimiter):
    if count == 1:
       generalfunctions.writetext(playlist_path, "#EXTM3U")

    #line = "#EXTINF:" + str(length) + "," + podcast_title + " - " + episode + " - " + dateString
    line = "#EXTINF:" + str(length) + "," + episode + " - " + dateString
    generalfunctions.writetext(playlist_path, line)

    if path_name[0:4].lower() == "http":
       line = ""
    else:
       line = "file://"

    playlist_path_name = line
    path_name_split = path_name.split(directory_delimiter)

    i=0
    first=1
    if playlist_path_name == "":
       first = 0
    for part in path_name_split:
        if i >= first:
           if i >= 1:
              if first == 1:
                 part = generalfunctions.html_encode(part)
                 part = generalfunctions.samba_encode(part)

           playlist_path_name += directory_delimiter + part
        i = i + 1

    if playlist_path_name[0:5].lower() == "/http":
       playlist_path_name = playlist_path_name[1:]

    line = playlist_path_name
    generalfunctions.writetext(playlist_path, line)


def download(url, path, overwrite, querystringtracking, proxy, useragent):
    downloaded = 999

    try:
      message = "Downloading: '" + url + "'"
      downloaded = generalfunctions.download(url, path, overwrite, querystringtracking, proxy, useragent, False, False)
      if downloaded <= 30:
         message=message+" using "
         if downloaded == 1:
            message=message+" exists"
         if downloaded == 2:
            message=message+" is empty"
         if downloaded == 10:
            message=message+" request (no proxy)"
         if downloaded == 20:
            message=message+" wget (no proxy)"
         if downloaded == 30:
            message=message+" request (with proxy)"
         log.log(True, 'DEBUG', message)
      else:
         config.exception_count += 1
         log.log(True, 'ERROR', message)
         print(message)

         message = "FAILED: "
         if downloaded == 999:
             message = message + "Return code: "
         else:
             message = message + "HTTP status code: "
         message = message + str(downloaded)

         log.log(True, 'ERROR', message)
         print(message)


    except Exception as e:
       config.exception_count += 1
       message = "Function: download: " + str(url)
       log.log(True, 'ERROR', message)
       message = str(e)
       log.log(True, 'ERROR', message)

    return downloaded

def strip_tracking(url):
    prefixes = config.file["prefix"]
    for prefix in prefixes:
        prefixenabled = bool(prefix["enabled"])
        prefixurl = str(prefix["url"])

        if not prefixenabled:
           url = url.replace(prefixurl , '')

        url = url.replace("https://https://", "https://")
        url = url.replace("http://http://", "http://")
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

def livestream(feed_url, feed_id, feed_title, playlist_path, playlisttxt_path, livefeed, podping):
    try:
       tzpretty = str(config.file["settings"]["timezone"])
       now = generalfunctions.now()
       nowTZ = generalfunctions.date_to_tz(now, tzpretty)
       nowseconds = generalfunctions.to_timestamp(nowTZ)
       nowstring = generalfunctions.format_dateYYYMMDDHHMM(nowTZ)
       formatpretty = "%H:%M %m/%d/%Y"
       tomorrowTZ = generalfunctions.tomorrow()
       message = feed_url + ' not live now'

       lits = None

       # TODO
       #lits = get_liveitems_api(feed_id)
       #lits = lits["items"]

       try:
          xml = loadXML_podcast(feed_url, feed_title)
          lits = get_liveitems(xml, 'https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md')
          if lits == None:
             lits = get_liveitems(xml, 'https://podcastindex.org/namespace/1.0')

       except Exception as e:
           config.exception_count += 1
           message = 'Function: livestream (loadXML): ' + str(e)
           log.log(True, 'ERROR', message)

       if lits != None and len(lits) > 0:
          for lit in lits:
              message = feed_url + ' not live now'
              prefix = prefix_stream
              onair = False

              status = get_liveitem_status(lit)
              start = get_liveitem_start(lit)
              end = get_liveitem_end(lit)
              title = get_liveitem_title(lit)
              url = get_liveitem_url(lit)

              status = status.lower()
              if url == "":
                 url = "<not set>"

              if start != "":
                 startdate = generalfunctions.string_to_date(start)
                 startdateTZ = generalfunctions.date_to_tz(startdate, tzpretty)
                 startdatestring = generalfunctions.format_dateYYYMMDDHHMM(startdateTZ)
                 startdatepretty = startdateTZ.strftime(formatpretty)
                 startdateseconds = generalfunctions.to_timestamp(startdateTZ)

                 live_announce_hours = int(config.file["settings"]["announceLive"])
                 live_announce_seconds = live_announce_hours * 3600
                 announceseconds = nowseconds + live_announce_seconds
                 announcedate = generalfunctions.timestamp_to_date(announceseconds)
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
                    message = feed_title + ' - ' + title + ' at ' + startdatepretty
                    if startdateTZ.date() == nowTZ.date():
                       message = feed_title + ' - ' + title + ' today at ' + str(startdateTZ.time())
                    if startdateTZ.date() == tomorrowTZ.date():
                       message = feed_title + ' - ' + title + ' tomorrow at ' + str(startdateTZ.time())
                    if not livefeed:
                       message += ' on ' + url
                       generalfunctions.writetext(playlisttxt_path, prefix + message)
                 if enddatestring != "":
                    leadindateTZ = generalfunctions.deltaminutes(startdateTZ, live_leadin)
                    leadoutdateTZ = generalfunctions.deltaminutes(enddateTZ, live_leadout)
                    if podping or (not podping and status == "live" and (leadindateTZ <= nowTZ and leadoutdateTZ >= nowTZ)):
                       prefix = prefix_live
                       message = feed_title + ' - ' + title + ' NOW'
                       if not livefeed:
                          message += ' on ' + url
                       onair = True

              if onair:
                 if not livefeed:
                    config.count_newpodcasts += 1
                    generalfunctions.writetext(playlisttxt_path, prefix + message)
                    addto_playlist_m3u(playlist_path, url, feed_title, title, 0, "NOW", config.count_newpodcasts, "/")
                 if verbosity:
                    print(message)

    except Exception as e:
        config.exception_count += 1
        message = 'Function: livestream: ' + str(e)
        log.log(True, 'ERROR', message)
        print(message)

def loadXML_podcast(feed_url, feed_title):
    root = None
    path = None
    try:
       fd, path = tempfile.mkstemp()
       downloaded = generalfunctions.download_wget(feed_url, path)

       if downloaded == 0:
          content = generalfunctions.readtext(path)
          tree = ET.parse(path)
          root = tree.getroot()

    except Exception as e:
        config.exception_count += 1
        message = 'Function: loadXML_podcast (' + feed_title + '): ' + str(e)
        log.log(True, 'ERROR', message)
        print(message)
    finally:
       if os.path.exists(path):
          os.remove(path)
    return root

def get_liveitems_api(feedId):
    PIurl = config.file["podcastindex"]["url"]
    url = PIurl + "episodes/live/byfeedid?id=" + str(feedId) + "&max=" + str(number_of_episodes)
    url = PIurl + "episodes/live/byfeedid?id=" + str(feedId)
    url = PIurl + "episodes/live?pretty"
    lits = PIfunctions.request(url)
    if lits == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    return lits

def get_liveitems(root, namespace):
    podcast = {'podcast': namespace}
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
    url = PIurl + "podcasts/byfeedid?id=" + str(feedId) + "&pretty"
    search_result = PIfunctions.request(url)
    if search_result == None:
       config.exception_count += 1
       message = 'No data returned from podcastindex API call: ' + url
       log.log(True, 'ERROR', message)
       print(message)
    else:
       status = generalfunctions.to_boolean(search_result['status'])
       if status:
          if len(search_result['feed']) > 0:
             feed_url = search_result['feed']['url']
          else:
             feed_url = ""
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

def check_podcast_feed(title, feedId, feedurl, playlisttxt_path, verbose):
    current = False
    feedurlPI = pi_search_podcast_by_id(int(feedId))
    if feedurlPI == None:
       message = 'Feed url of \'' + title + '\' can\'t be checked.'
       log.log(True, 'ERROR', message)
       message = prefix_error+message
       print(message)
    else:
       if feedurl == feedurlPI:
          current = True
          message = 'Checked feed url of ' + title + ' - ' + feedurl
       else:
          if feedurlPI == "":
             message = prefix_list + title + " - feed url has been removed. *** Please edit podcast list"
          else:
             message = prefix_list + title + " - feed url has changed from '" + feedurl + "' to '" + str(feedurlPI) + "' *** Please edit podcast list"
          log.log(True, 'ERROR', message)
          generalfunctions.writetext(playlisttxt_path, message)
          print(message)
    return current

    if not current:
       log.log(False, 'WARN', message)
       generalfunctions.writetext(playlisttxt_path, message)
       print(message)

    if verbose:
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

def pi_api(api_url):
    api_response = None
    if api_url == "ALL":
       api_url = "episodes/byfeedid?id=920666"
       print("Example: python " + sys.argv[0] + " API " + api_url)
    else:
       PIurl = config.file["podcastindex"]["url"]
       url = PIurl + api_url
       api_response = PIfunctions.request(url)
       if api_response == None:
          message = 'No data returned from podcastindex API call: ' + url
          log.log(True, 'ERROR', message)
          print(message)
    return api_response


def process_file(data, data_path, number_of_episodes, playlisttxt_path, playlist_path, playlist_client_path, overwrite, mode, podcast_to_process, querystringtracking, proxy, useragent):
    try:
        podping_live = False
        if mode == "PP_LIVE":
           podping_live = True

        for podcast_data in data['podcastlist']:
            feedurl = "-"
            verbose = False
            if mode == "CHECK":
               verbose = True

            if podcast_data["id"][:1] != '#':
               if podcast_to_process == "ALL" or str(podcast_to_process) == podcast_data["id"] or str(podcast_to_process) == podcast_data["title"] or str(podcast_to_process) == podcast_data["feed"]:

                  # logging
                  message = 'Processing podcast \'' + podcast_data["title"] + '\''
                  if verbosity:
                     print('==========================================================')
                     print(message)
                     print('==========================================================')
                  log.log(False, 'INFO', message)

                  if mode == "LIST":
                     print(podcast_data['title'] + ' ' + podcast_data['id'])

                  if mode == "CHECK" or mode == "PROCESS" or mode == "LIVE" or mode == "PP_LIVE":
                     currentFeed = check_podcast_feed(podcast_data['title'], podcast_data['id'], podcast_data['feed'], playlisttxt_path, verbose)

                  if mode != "LIST" and currentFeed:
                     if mode == "LIVE" or mode == "PP_LIVE" or mode == "PROCESS":
                        livefeed = bool(podcast_data['live'])

                        livestream(podcast_data['feed'], podcast_data['id'], podcast_data['title'], playlist_path, playlisttxt_path, livefeed, podping_live)

                     if mode == "PROCESS":
                        process_podcast(podcast_data, number_of_episodes, data_path, playlisttxt_path, playlist_path, playlist_client_path, overwrite, mode, querystringtracking, proxy, useragent)
            else:
               if podcast_to_process == "ALL":
                  message = 'Skipping podcast \'' + podcast_data["title"] + '\''
                  log.log(False, 'INFO', message)

        if config.count_newpodcasts > 0:
           generalfunctions.writetext(playlist_path, "")

    except Exception as e:
        config.exception_count += 1
        message = 'Function: process_file: ' + str(e)
        log.log(True, 'ERROR', message)
        print(message)


def process_podcast(podcast_data, number_of_episodes, data_path, playlisttxt_path, playlist_path, playlist_client_path, overwrite, mode, querystringtracking, proxy, useragent):
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
                 downloaded = download(url, path, overwrite, False, proxy, useragent)
                 if download_result(downloaded) >= 100:
                    config.exception_count += 1
                    message = 'Podcast image (' + url + ') NOT downloaded. Returncode: ' + str(downloaded)
                    log.log(True, 'ERROR', message)

              # artwork
              url = feed["artwork"]
              if url != None and url != '':
                 path = os.path.basename(url)
                 path = os.path.join(podcast_path, path)
                 downloaded = download(url, path, overwrite, False, proxy, useragent)
                 if download_result(downloaded) >= 100:
                    config.exception_count += 1
                    message = 'Podcast artwork (' + url + ') not downloaded. Returncode: ' + str(downloaded)
                    log.log(True, 'ERROR', message)

              # process episodes
              process_episodes(podcast_data["id"], number_of_episodes, podcast_data["title"], podcast_path, playlisttxt_path, playlist_path, podcast_client_path, overwrite, querystringtracking, proxy, useragent)

    except Exception as e:
        config.exception_count += 1
        message = 'Function: process_podcast (' + str(podcast_data["title"]) + '): ' + str(e)
        log.log(True, 'ERROR', message)
        print(message)


def process_chapter(chapter, path, overwrite, querystringtracking, proxy, useragent):
    try:
        # logging
        chapter_title = str(chapter["title"][0:80])
        message = 'Processing chapter \'' + chapter_title + '\''
        if verbosity:
           print(message)
        log.log(False, 'INFO', message)

        # create directory for chapter
        chapter_title = generalfunctions.sanitize_path(chapter_title, False)
        chapter_title = chapter_title.replace('/', '')
        chapter_directory = str(chapter["startTime"]) + '-' + chapter_title
        path = os.path.join(path, chapter_directory)
        generalfunctions.create_directory(path)
        chapter_path = path

        # write json data
        path = 'data.json'
        path = os.path.join(chapter_path, path)
        generalfunctions.write_file(path, json.dumps(chapter, indent = 2))

        # image
        if "img" in chapter and chapter["img"] != None and chapter["img"] != "":
            url = chapter["img"]
            path = os.path.basename(url)
            file_name = generalfunctions.file_name_noextension(path)
            file_extension = generalfunctions.file_extension(path)
            path = os.path.join(chapter_path, path)
            downloaded = download(url, path, overwrite, querystringtracking, proxy, useragent)

        # url
        if "url" in chapter and chapter["url"] != None and chapter["url"] != "":
            url = chapter["url"]
            path = os.path.basename(url)
            file_name = generalfunctions.file_name_noextension(path)
            file_extension = generalfunctions.file_extension(path)
            if file_extension == ".jpg" or file_extension == ".png" or file_extension == ".pdf" or file_extension == ".mp3":
               path = os.path.join(chapter_path, path)
               downloaded = download(url, path, overwrite, querystringtracking, proxy, useragent)
               if download_result(downloaded) >= 100:
                  config.exception_count += 1
                  message = "FAILED: '" + url + "'"
                  log.log(True, 'ERROR', message)
                  print(message)

    except Exception as e:
        config.exception_count += 1
        message = "Function: process_chapter: '" + chapter + "'"
        log.log(True, 'ERROR', message)
        print(message)
        message = "Function: process_chapter: '" + path + "'"
        log.log(True, 'ERROR', message)
        print(message)
        message = "Function: process_chapter: '" + str(e)
        log.log(True, 'ERROR', message)
        print(message)


def exception(function, podcast_title, title, url, path, exception):
        config.exception_count += 1
        message = "Function: " + function + ": '" + podcast_title + "'"
        log.log(True, 'ERROR', message)
        print(message)
        message = "Function: " + function + ": '" + title + "'"
        log.log(True, 'ERROR', message)
        print(message)
        message = "Function: " + function + ": '" + url + "'"
        log.log(True, 'ERROR', message)
        print(message)
        message = "Function: " + function + ": '" + path + "'"
        log.log(True, 'ERROR', message)
        print(message)
        message = "Function: process_episode: " + exception
        log.log(True, 'ERROR', message)
        print(message)


def process_episode(podcast_title, episode, path, overwrite, playlisttxt_path, playlist_path, podcast_client_path, querystringtracking, proxy, useragent):
    try:
        title = episode["title"]
        title = generalfunctions.sanitize_path(title, False)
        title = title.replace('/', '')
        length = episode["duration"]
        timestamp_episode = int(episode["datePublished"])
        date_episode = generalfunctions.timestamp_to_date(timestamp_episode)
        dateString = generalfunctions.format_date(date_episode, config.file["settings"]["formatdatetime"])

        # logging
        message = 'Processing episode \'' + title + '\''
        if verbosity:
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

    except Exception as e:
        exception("process_episode (logging)", podcast_title, title, url, path, str(e))

    # download episode assets
    try:
        # image
        url = episode["image"]
        url_split = url.rsplit('?', -1)
        url = url_split[0]
        if url != None and url != '':
            path = os.path.basename(url)
            #print(episode_path)
            path = os.path.join(episode_path, path)
            downloaded = download(url, path, overwrite, querystringtracking, proxy, useragent)

    except Exception as e:
        exception("process_episode (image)", podcast_title, title, url, path, str(e))

    try:
        # enclosure url
        url = episode["enclosureUrl"]
        if url != None and url != '':
           url = episode["enclosureUrl"]

           url = strip_tracking(url)

           enclosure_file = os.path.basename(url)
           enclosure_file = enclosure_file.split('?')[0]
           enclosure_path = os.path.join(episode_path, enclosure_file)
           enclosure_client_path = os.path.join(episode_client_path, enclosure_file)

           downloaded = download(url, enclosure_path, overwrite, querystringtracking, proxy, useragent)
           if download_result(downloaded) == 0:
              message = "Downloaded: " + enclosure_path
              log.log(False, 'INFO', message)
              config.count_newpodcasts += 1
              generalfunctions.writetext(playlisttxt_path, prefix_file + enclosure_client_path)
              addto_playlist_m3u(playlist_path, enclosure_client_path, podcast_title, title, length, dateString, config.count_newpodcasts, "/")
           if download_result(downloaded) >= 100:
              config.exception_count += 1
              message = "Podcast '" + podcast_title + " - " + title + "' not downloaded. Returncode: " + str(downloaded)
              log.log(True, 'ERROR', message)
              generalfunctions.writetext(playlisttxt_path, prefix_error + message)

    except Exception as e:
        exception("process_episode (enclosure)", podcast_title, title, url, path, str(e))

    try:
        # chapters
        url = episode["chaptersUrl"]
        if url != None and url != '':
            path = os.path.basename(url)
            path = os.path.join(episode_path, path)
            chapter_file = generalfunctions.strip_querystring_path(path)
            downloaded = download(url, chapter_file, True, querystringtracking, proxy, useragent)
            if download_result(downloaded) == 0:

               # create directory for chapters
               path = os.path.join(episode_path, 'Chapters')
               generalfunctions.create_directory(path)
               chapter_path = path

               # read chapters
               chapters = generalfunctions.read_json(chapter_file)

               if chapters != None and chapters != "":
                  if chapters == "ERROR":
                     config.exception_count += 1
                     message = "Chapter file is not valid JSON: '" + chapter_file + "'"
                     log.log(True, 'ERROR', message)
                     print(message)
                  else:
                     for chapter in chapters["chapters"]:
                         toc = True
                         for key,value in chapter.items():
                             if key == "toc":
                                toc = bool(value)
                         if toc:
                            process_chapter(chapter, chapter_path, overwrite, querystringtracking, proxy, useragent)
            else: 
               config.exception_count += 1
               message = 'Podcast chapters not downloaded. Returncode: ' + str(downloaded)
               message = "Podcast '" + podcast_title + " - " + title + "' chapters not downloaded. Returncode: " + str(downloaded)
               log.log(True, 'ERROR', message)
               print(message)

    except Exception as e:
        exception("process_episode (chapters)", podcast_title, title, url, path, str(e))

    try:
        # transcript
        url = episode["transcriptUrl"]
        if url != None and url != '':
            path = os.path.basename(url)
            path = os.path.join(episode_path, path)
            downloaded = download(url, path, True, querystringtracking, proxy, useragent)

    except Exception as e:
        exception("process_episode (transcripts)", podcast_title, title, url, path, str(e))


def process_episodes(feedId, number_of_episodes, feedTitle, path, playlisttxt_path, playlist_path, podcast_client_path, overwrite, querystringtracking, proxy, useragent):
    try:
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
               process_episode(feedTitle, episode, path, overwrite, playlisttxt_path, playlist_path, podcast_client_path, querystringtracking, proxy, useragent)

    except Exception as e:
        config.exception_count += 1
        message = 'Function: process_episodes: ' + str(e)
        log.log(True, 'ERROR', message)
        print(message)


def aggregate(mode, podcast_to_process, number_of_episodes):
    try:
        config.exception_count = 0
        config.count_newpodcasts = 0
        datadir = config.file["directory"]["data"]
        playlist_client_path = config.file["directory"]["playlist"]
        podcastlist_file = config.file["file"]["podcastlist"]

        proxy = None
        useproxy = bool(config.file["settings"]["useproxy"])
        if useproxy:
           proxy = config.file["settings"]["proxy"]

        useragent = config.file["settings"]["useragent"]
        querystringtracking = bool(config.file["querystringtracking"]["enabled"])

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
        playlisttxt_path = playlist_path.replace('m3u', 'txt')
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
           process_file(data, datadir, number_of_episodes, playlisttxt_path, playlist_path, playlist_client_path, overwrite, mode, podcast_to_process, querystringtracking, proxy, useragent)


        if verbosity:
           print('==========================================================')

           if config.count_newpodcasts > 0:
              newpodcasts = generalfunctions.read_file(playlisttxt_path)
              if newpodcasts == None:
                 print('File ' + playlisttxt_path + ' does not exists')
              else:
                 print(newpodcasts)
              print('==========================================================')

        message = 'Finished: ' + str(config.exception_count) + ' errors.'
        if config.exception_count > 0:
           message += ' See ' + config.log_error_path 
           if verbosity:
              print(message)
              print('==========================================================')

        if mode == 'PROCESS':
           message = str(config.count_newpodcasts) + ' new podcast'
           if config.count_newpodcasts == 0 or config.count_newpodcasts >= 2:
              message += 's'
           message += '.'
           if verbosity:
              log.log(False, 'INFO', message)
              print(message)
              print('==========================================================')

    except Exception as e:
        config.exception_count += 1
        message = 'Function: aggregate: ' + str(e)
        print(message)
        log.log(True, 'ERROR', message)


try:
    config.read() 

    prefix_error = config.file["settings"]["prefix_error"]
    prefix_file = config.file["settings"]["prefix_file"]
    prefix_stream = config.file["settings"]["prefix_stream"]
    prefix_live = config.file["settings"]["prefix_live"]
    prefix_list = config.file["settings"]["prefix_list"]

    number_of_episodes = config.file["settings"]["numberOfEpisodes"]
    verbose = config.file["settings"]["verbosity"]

    mode = "PROCESS"
    podcast_to_process = "ALL"

    if len(sys.argv) == 5:
       mode = sys.argv[1]
       podcast_to_process = sys.argv[2]
       number_of_episodes = sys.argv[3]
       verbose = sys.argv[4]

    verbosity = True
    if int(verbose) == 0:
       verbosity = False

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
       print ('Usage: ' + sys.argv[0] + ' [LIST | SEARCH | API | CHECK | LIVE | PP_LIVE | PROCESS] [ALL|<search term>|<podcastindex-id>|<feedurl>] [numberOfEpisodes] [verbosity 0|1]')
    else:
       if mode == "PROCESS" or mode == "LIST" or mode == "SEARCH" or mode == "CHECK" or mode == "LIVE" or mode == "PP_LIVE":
          aggregate(mode, podcast_to_process, number_of_episodes)
       if mode == "API":
          response = pi_api(podcast_to_process)
          if response != None:
             fd, path = tempfile.mkstemp()
             result = generalfunctions.writetext(path, str(response))
             if result == 0:
                print("Response is in: " + path)


except Exception as e:
    config.exception_count += 1
    message = 'Function: aggregate: ' + str(e)
    log.log(True, 'ERROR', message)
    print(message)
