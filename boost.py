#!/usr/bin/env python3

import sys
import os
import json
import requests
import subprocess

import PIfunctions
import configuration
import generalfunctions

def podcastdata(feedId, log_path):
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl  + "podcasts/byfeedid?id=" + str(feedId)
    #generalfunctions.log(log_path, url, False, True)
    feed_result = PIfunctions.request(url, log_path)
    return feed_result

def podcast_value(feedId, log_path):
    value = None
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl + "value/byfeedid?id=" + str(feedId) + "&pretty"
    result = PIfunctions.request(url, log_path)
    value = result['value']['destinations']
    return value

def episode_value(feedId, episode_nr, log_path):
    value = None
    PIurl = configuration.config["podcastindex"]["url"]
    url = PIurl + "episodes/byfeedid?id=" + str(feedId) + "&max=1000" + "&pretty"
    episodes_result = PIfunctions.request(url, log_path)
    for episode in episodes_result['items']:
        if episode['episode'] == str(episode_nr) or str(episode_nr) in episode['title']:
           value = episode['value']['destinations']
    if value == None:
       value = podcast_value(feedId, log_path)
    return value

def process_file(mode, data, episodes_nr, podcast_to_process, timestamp, amount, boostagram, podcastlist_file, log_path):
    for podcast_data in data['podcastlist']:
        feedurl = "-"

        if podcast_data["id"][:1] != '#':
           if podcast_to_process == "ALL" or str(podcast_to_process) == podcast_data["id"] or str(podcast_to_process) == podcast_data["feed"]:
              valueblock = episode_value(podcast_data['id'], episodes_nr, log_path)
              if valueblock != None:
                 sendboostagramscript = configuration.config["file"]["sendboostagram"]
                 if mode == "BOOST" or mode == "VALUE":
                    print(podcast_data['title'])
                    for recipient in valueblock:
                        if recipient['type'] == 'node':
                           if mode == "BOOST":
                              print('Boosting ' + recipient['name'])
                              command = sendboostagramscript + ' ' + ''
                              subprocess.call(command, shell=True)
                           if mode == "VALUE":
                              print(recipient['name'] + ' ' + str(recipient['split']))
              else:
                 message = 'No value block in index'
                 print(message)
                 generalfunctions.log(log_path, message, False, False)
        else:
           message = 'Skipping podcast \'' + podcast_data["title"] + '\''
           generalfunctions.log(log_path, message, False, False)


try:
    podcast_to_process = "--help"
    if len(sys.argv) == 7:
       mode = sys.argv[1]
       podcast_to_process = sys.argv[2]
       episode_nr = sys.argv[3]
       timestamp = sys.argv[4]
       amount = sys.argv[5]
       boostagram = sys.argv[6]
    if len(sys.argv) == 4:
       mode = sys.argv[1]
       podcast_to_process = sys.argv[2]
       episode_nr = sys.argv[3]
       timestamp = 0
       amount = 0
       boostagram = ''

    if str(podcast_to_process) == "-h" or podcast_to_process == "--help":
       print ('Usage: ' + sys.argv[0] + ' VALUE|BOOST <podcastindex-id> <episode nr> [<timestamp> <amount> <message>]')
    else:
       configuration.read() 
       datadir = configuration.config["directory"]["data"]
       log_path = os.path.join(datadir, configuration.config["directory"]["log"])
       podcastlist_file = configuration.config["file"]["podcastlist"]

       now = generalfunctions.now()
       dateString = generalfunctions.format_dateYYYMMDDHHMMSS(now)

       log_path = os.path.join(log_path, dateString+'.log')
       data = generalfunctions.read_json(podcastlist_file, log_path)
       process_file(mode, data, episode_nr, podcast_to_process, timestamp, amount, boostagram, podcastlist_file, log_path)

except Exception as e:
    message = e
    message = 'Function: ' + function.__name__ + ': ' + str(e)
    generalfunctions.log(log_path, message, True, False)
    print(message)
