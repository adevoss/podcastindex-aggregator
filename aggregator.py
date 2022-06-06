#!/usr/bin/env python3

import configuration
import PIfunctions
import generalfunctions
import sys
import os
import json
import tempfile
import requests
import xml.etree.cElementTree as ET

def livestream(feed, log_path):
    now = generalfunctions.now()
    nowstring = generalfunctions.format_dateYYYMMDDHHMM(now)

    xml = loadXML_podcast(feed)
    lits = get_liveitems(xml)
    for lit in lits:
        onair = False
        start = get_liveitem_start(lit)
        end = get_liveitem_end(lit)
        title = get_liveitem_title(lit)
        url = get_liveitem_url(lit)
        message = title + ' at ' + start + ' on ' + url

        if start != "":
           startdatestring = generalfunctions.format_dateIS8601(start, "%Y%m%d%H%M")
        if end != "":
           enddatestring = generalfunctions.format_dateIS8601(end, "%Y%m%d%H%M")

        if startdatestring != "":
           if enddatestring == "":
              if startdatestring <= nowstring:
                 onair = True
           else:
              if enddatestring >= nowstring:
                 onair = True

        if onair:
           generalfunctions.log(log_path, message, False)
           print(message)

def loadXML_podcast(feed):
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
    lit = ""
    if root == "":
       pass
    else:
       channel = root.find('channel')
       lits = channel.findall('podcast:liveItem', podcast)
    return lits

def get_liveitem_start(lit):
    start = ""
    if lit == "":
       pass
    else:
       start = lit.attrib.get('start')
    return start

def get_liveitem_end(lit):
    end = ""
    if lit == "":
       pass
    else:
       end = lit.attrib.get('end')
    return end

def get_liveitem_title(lit):
    title = "-"
    if lit == "":
       pass
    else:
       if lit.find('title') != None:
          title = lit.find('title').text
    return title

def get_liveitem_url(lit):
    url = ""
    if lit == "":
       pass
    else:
       url = lit.find('enclosure').attrib.get('url')
    return url

def search_podcast(feed):
    url = "https://api.podcastindex.org/api/1.0/podcasts/byfeedurl?url=" + feed + "&pretty"
    search_result = PIfunctions.request(url)
    status = generalfunctions.to_boolean(search_result['status'])
    if status:
       podcast_id = search_result['feed']['id']
    else:
       podcast_id = ""
    return podcast_id

def podcast(feedId):
    url = configuration.config["podcastindex"]["url"] + "/podcasts/byfeedid?id=" + str(feedId)
    feed_result = PIfunctions.request(url)
    return feed_result

def episodes(feedId):
    number_of_episodes = int(configuration.config["settings"]["numberOfEpisodes"])
    url = "https://api.podcastindex.org/api/1.0/episodes/byfeedid?id=" + str(feedId) + "&max=" + str(number_of_episodes)
    episodes_result = PIfunctions.request(url)
    return episodes_result

def process_file(data, data_path, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process):
    for podcast_data in data['podcastlist']:
        if podcast_to_process == "TITLE":
           print(podcast_data['title'] + ' ' + podcast_data['id'])

        if podcast_to_process == "FEED":
           feed = podcast(podcast_data["id"])["feed"]["url"]
           print(podcast_data['title'] + ' ' + str(feed))
        else:
           if podcast_data["id"][:1] != '#':
              if podcast_to_process == "ALL":
                 process_podcast(podcast_data, data_path, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process)
              else:
                 if str(podcast_to_process) == podcast_data['id']:
                    message = 'Processing podcast \'' + podcast_data['title'] + '\''
                    generalfunctions.log(log_path, message, False)
                    process_podcast(podcast_data, data_path, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process)
           else:
              if podcast_to_process == "ALL":
                 message = 'Skipping podcast \'' + podcast_data["title"] + '\''
                 generalfunctions.log(log_path, message, False)

def process_podcast(podcast_data, data_path, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process):
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
        generalfunctions.log(log_path, message, False)

        feed = podcast(podcast_data["id"])["feed"]

        # livestream
        livestream(feed["url"], log_path)

        # download feed assets
        path = 'data.json'
        path = os.path.join(podcast_path, path)
        generalfunctions.write_file(path, json.dumps(feed, indent = 2))

        # image
        url = feed["image"]
        path = os.path.basename(url)
        path = os.path.join(podcast_path, path)
        generalfunctions.download(url, path, log_path, overwrite)

        # process episodes
        process_episodes(podcast_data["id"], podcast_data["title"], podcast_path, log_path, playlist_path, podcast_client_path, overwrite)
    except Exception as e:
        message = e
        generalfunctions.log(log_path, message, True)
        print(message)

def process_chapter(chapter, path, log_path, overwrite):
    # logging
    chapter_title = str(chapter["title"][0:50])
    message = 'Processing chapter \'' + chapter_title + '\''
    print(message)
    generalfunctions.log(log_path, message, False)

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
            # don't overwrite files
            if os.path.isfile(path):
                now = generalfunctions.now()
                dateFormatted = generalfunctions.format_dateYYYMMDDHHMM(now)
                path = os.path.join(chapter_path, file_name+'-'+dateFormatted+file_extension)

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
    generalfunctions.log(log_path, message, False)

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
        downloaded = generalfunctions.download(url, path, log_path, overwrite)
        if downloaded:
           chapter_file = path

           # create directory for chapters
           path = os.path.join(episode_path, 'Chapters')
           generalfunctions.create_directory(path)
           chapter_path = path

           # download chapters
           chapters = generalfunctions.read_json(chapter_file, log_path)
           #print(chapters)
           if chapters != None and chapters != '':
              for (chapter) in chapters["chapters"]:
                  process_chapter(chapter, chapter_path, log_path, overwrite)

    # transcript
    url = episode["transcriptUrl"]
    if url != None and url != '':
        path = os.path.basename(url)
        path = os.path.join(episode_path, path)
        generalfunctions.download(url, path, log_path, True)

def process_episodes(feedId, feedTitle, path, log_path, playlist_path, podcast_client_path, overwrite):
    # create directory for episodes
    path = os.path.join(path, 'Episodes')
    podcast_client_path = os.path.join(podcast_client_path, 'Episodes')
    generalfunctions.create_directory(path)

    episodes_data = episodes(feedId)["items"]
    # print(json.dumps(episodes_data, indent = 2))
    for (episode) in episodes_data:
        process_episode(episode, path, overwrite, log_path, playlist_path, podcast_client_path)

def aggregate(podcast_to_process):
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
           message = 'Processing file \''+ podcastlist_file + '\'' + ' at ' + dateString
           generalfunctions.log(log_path, message, False)
        else:
           message = 'Processing podcast \''+ podcast_to_process + '\'' + ' at ' + dateString

        if podcast_to_process[0:4].lower() == "http":
           message = 'Podcast feed \''+ podcast_to_process + '\'' + ' not in podcastindex'
           podcast_to_process = search_podcast(podcast_to_process)

        if podcast_to_process == "":
           pass
           #generalfunctions.log(log_path, message, False)
        else:

           # logging
           now = generalfunctions.now()
           data = generalfunctions.read_json(podcastlist_file, log_path)
           process_file(data, datadir, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process)

           if podcast_to_process == "ALL":
              dateString = generalfunctions.format_dateYYYMMDDHHMM(now)
              message = 'Done at ' + dateString
              generalfunctions.log(log_path, message, False)
#           else:
#              dateString = generalfunctions.format_dateYYYMMDDHHMMSS(now)
#              message = 'Done at ' + dateString
#              generalfunctions.log(log_path, message, False)

    except Exception as e:
        message = e
        #generalfunctions.log(log_path, message, True)


try:
    if len(sys.argv) == 2:
       podcast_to_process = sys.argv[1]
    else:
       podcast_to_process = "ALL"

    if podcast_to_process == "-h" or podcast_to_process == "--help":
       print ("Usage: sys.argv[0] [ALL|TITLE|FEED|<podcastindex-id>]")
    else:
       configuration.read() 
       aggregate(podcast_to_process)

except Exception as e:
    message = e
    #generalfunctions.log(log_path, message, True)
    print(message)

