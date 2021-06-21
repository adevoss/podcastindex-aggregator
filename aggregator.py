#!/usr/bin/env python3

import configuration
import PIfunctions
import generalfunctions
import sys
import os
import json

def podcast(feedId):
    url = configuration.config["podcastindex"]["url"] + "/podcasts/byfeedid?id=" + str(feedId)
    feed_result = PIfunctions.request(url)
    return feed_result

def episodes(feedId):
    url = "https://api.podcastindex.org/api/1.0/episodes/byfeedid?id=" + str(feedId)
    episodes_result = PIfunctions.request(url)
    return episodes_result

def process_file(data, data_path, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process):
    for podcast_data in data['podcastlist']:
        if podcast_to_process == "ALL" or podcast_to_process in podcast_data['title']:
           process_podcast(podcast_data, data_path, log_path, playlist_path, playlist_client_path, overwrite)

def process_podcast(podcast_data, data_path, log_path, playlist_path, playlist_client_path, overwrite):
    if podcast_data["id"][:1] != '#':
       # create directory for podcast
       podcast_path = os.path.join(data_path, podcast_data["directory"], podcast_data["title"])
       podcast_client_path = os.path.join(playlist_client_path, podcast_data["directory"], podcast_data["title"])
       generalfunctions.create_directory(podcast_path)

       # logging
       message = 'Processing podcast \'' + podcast_data["title"] + '\''
       print('==========================================================')
       print(message)
       print('==========================================================')
       generalfunctions.log(log_path, message)

       # download feed assets
       feed = podcast(podcast_data["id"])["feed"]
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

def process_chapter(chapter, path, log_path, overwrite):
    # logging
    chapter_title = str(chapter["title"][0:50])
    message = 'Processing chapter \'' + chapter_title + '\''
    print(message)
    generalfunctions.log(log_path, message)

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
    generalfunctions.log(log_path, message)

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
        enclosure_path = os.path.join(episode_path, enclosure_file)
        enclosure_client_path = os.path.join(episode_client_path, enclosure_file)
        downloaded = generalfunctions.download(url, enclosure_path, log_path, overwrite)
        if downloaded:
           generalfunctions.log(playlist_path, enclosure_client_path)

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
        generalfunctions.download(url, path, log_path, overwrite)

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
    datadir = configuration.config["directory"]["data"]
    playlist_client_path = configuration.config["directory"]["playlist"]
    podcastlist_file = configuration.config["file"]["podcastlist"]

    # create directory
    log_path = os.path.join(datadir, configuration.config["directory"]["log"])
    generalfunctions.create_directory(log_path)
    playlist_path = os.path.join(datadir, configuration.config["directory"]["play"])
    generalfunctions.create_directory(playlist_path)

    now = generalfunctions.now()
    dateString = generalfunctions.format_dateYYYMMDDHHMM(now)
    log_path = os.path.join(log_path, dateString+'.log')
    playlist_path = os.path.join(playlist_path, dateString+'.m3u')
    overwrite = False

    # logging
    message = 'Processing file \''+ podcastlist_file + '\'' + ' at ' + dateString
    generalfunctions.log(log_path, message)

    data = generalfunctions.read_json(podcastlist_file, log_path)
    process_file(data, datadir, log_path, playlist_path, playlist_client_path, overwrite, podcast_to_process)

    # logging
    now = generalfunctions.now()
    dateString = generalfunctions.format_dateYYYMMDDHHMM(now)
    message = 'Done at ' + dateString
    generalfunctions.log(log_path, message)



if len(sys.argv) == 2:
    podcast_to_process = sys.argv[1]
else:
    podcast_to_process = "ALL"

configuration.read() 
aggregate(podcast_to_process)