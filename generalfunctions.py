#!/usr/bin/env python3

import logging
import csv
import os
import requests
import json
import pathlib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser as DP
import pytz


def log(path, message, isError, isDebug):
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(path)])

        if isError:
           logging.error(message)
        else:
           if isDebug:
              logging.debug(message)
           else:
              logging.info(message)

    except Exception as e:
        logging.error(str(e))
        #print(e)

def writetext(path, message):
    try:
        if os.path.isfile(path):
            with open(path, "a") as outfile:
                outfile.write("\n")
        else:
            with open(path, 'w') as outfile: 
                pass

        with open(path, "a") as outfile:
            outfile.write(message)

    except Exception as e:
        logging.error(str(e))

def create_directory(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def download(url, path, log_path, overwrite):
    downloaded = False
    try:
        if url != None and url !='':
           if path != None and path !='':
              path = sanitize(path)
              if (os.path.isfile(path) and overwrite) or not os.path.isfile(path):
                 message = 'Downloading \'' + os.path.basename(path) + '\' ...'
                 print(message)
                 log(log_path, message, False, False)
                 r = requests.get(url)
                 with open(path, 'wb') as outfile:
                      outfile.write(r.content)
                 downloaded = True
           else:
              message = "path is empty"
              print(message)
              log(log_path, message, True, False)
        else:
           message = "url is empty"
           print(message)
           log(log_path, message, True, False)

    except Exception as e:
        log(log_path, str(e), True, False)
        print(e)

    return downloaded

def sanitize(path):
    sanitized = os.path.join(sanitize_path(os.path.dirname(path), False), sanitize_path(os.path.basename(path), True))
    return sanitized

def sanitize_path(pathFileName, isFileName):
    sanitized = pathFileName
    illegal = '{}\\'
    for char in illegal:
        sanitized = sanitized.replace(char, '')
    if isFileName:
        sanitized = sanitized.replace('/', '')
        sanitized = sanitized.replace('..', '.')
    return sanitized

def write_file(path, text):
    with open(path, "w") as outfile: 
        outfile.write(text)

def read_json(path, log_path):
    try:
       json_text = None
       with open(path, 'r', encoding="utf-8-sig") as openfile: 
            text = openfile.read()
            openfile.close()

       # strip BOM character
       text = text.lstrip('\ufeff')

       if '<!DOCTYPE HTML>' in text:
          message = 'Text is HTML not JSON.'
          print(message)
       else:
          json_text = json.loads(text)

    except Exception as e:
        json_text = None
        log(log_path, str(e), True, False)
        print(e)

    return json_text

def file_extension(path):
    extension = pathlib.Path(path).suffix
    return extension

def file_name_noextension(path):
    name = os.path.splitext(path)[0]
    return name

def format_dateIS8601(date, format):
    dateISO8601 = string_to_date(date)
    formatted = dateISO8601.strftime(format)
    return formatted

def string_to_date(date):
    dateISO8601 = DP.parse(date)
    return dateISO8601

def format_dateYYYMMDDHHMM(date):
    format = "%Y%m%d%H%M"
    formatted = date.strftime(format)
    return formatted

def format_dateYYYMMDDHHMMSS(date):
    format = "%Y%m%d%H%M%S"
    formatted = date.strftime(format)
    return formatted

def date_to_tz(date, tz):
    dateTZ = date.astimezone(pytz.timezone(tz))
    return dateTZ

def now():
    date = datetime.now()
    return date

def tomorrow():
    date = now() + timedelta(1)
    return date

def deltaminutes(date, delta):
    date = date + relativedelta(minutes=delta)
    return date

def to_epoch(date):
    epoch = date.timestamp()
    return epoch

def to_date(epoch):
    date = datetime.fromtimestamp(epoch)
    return date

def to_boolean(text):
    status = False
    if text.lower() == "true":
       status = True
    return status
