#!/usr/bin/env python3

import logging
import csv
import os
import requests
import wget
import json
import pathlib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser as DP
import pytz


def log_handler_file(filename):
    handler = logging.FileHandler(filename, mode='a', encoding='utf-8', delay=True)
    return handler

def writetext(path, message):
    if os.path.isfile(path):
        with open(path, "a") as outfile:
            outfile.write("\n")
    else:
        with open(path, 'w') as outfile: 
            pass

    with open(path, "a") as outfile:
        outfile.write(message)

def create_directory(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def bar_custom(current, total, width=80):
    print('Downloading: %d%% [%d / %d] bytes' % (current / total * 100, current, total))

def download(url, path, overwrite, querystringtracking, timeout_connect, timeout_read, progress=False, verbose=True):
    # 0 = success
    # 1 = already downloaded
    # 10 = failed
    downloaded = 10

    if url != None and url !='':
       if not querystringtracking:
          url = url.split('?')[0]
       if path != None and path !='':
          path = sanitize(path)
          if (os.path.exists(path) and overwrite) or not os.path.exists(path):
             message = 'Downloading \'' + os.path.basename(path) + '\' ...'
             if verbose:
                print(message)

             if not progress:
                r = requests.get(url, timeout=(timeout_connect,timeout_read))
                with open(path, 'wb') as outfile:
                     outfile.write(r.content)
             else:
                wget.download(url, out=path, bar=bar_custom)
             downloaded = 0
          else:
             downloaded = 1
       else:
          message = "path is empty"
          print(message)
    else:
       message = "url is empty"
       print(message)

    return downloaded

def sanitize(path):
    sanitized = os.path.join(sanitize_path(os.path.dirname(path), False), sanitize_path(os.path.basename(path), True))
    return sanitized

def sanitize_path(path, isFileName):
    sanitized = path
    illegal = '{}\\'
    for char in illegal:
        sanitized = sanitized.replace(char, '')
    if isFileName:
        sanitized = sanitized.replace('/', '')
        sanitized = sanitized.replace('..', '.')
    else:
        sanitized = sanitized.replace(' .', '.')
        sanitized = sanitized.replace('....', '')
        sanitized = sanitized.replace('...', '')
        sanitized = sanitized.replace('..', '')
        # remove '.' if last character of directory is '.'
        if sanitized[len(sanitized)-1] == '.':
           sanitized = sanitized[0:len(sanitized)-1]
    return sanitized

def read_file(path):
    text = None
    if os.path.exists(path):
       with open(path, "r") as file: 
           text = file.read()
    return text

def write_file(path, text):
    with open(path, "w") as outfile: 
        outfile.write(text)

def read_json(path):
    json_text = None
    with open(path, 'r', encoding="utf-8-sig") as openfile: 
         text = openfile.read()
         openfile.close()

    # strip BOM character
    text = text.lstrip('\ufeff')

    if '<!DOCTYPE HTML>' in text:
       message = 'Text is HTML not JSON.'
    else:
       json_text = json.loads(text)

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
