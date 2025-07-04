#!/usr/bin/env python3

import logging
import os
import requests
import subprocess
import json
import pathlib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser as DP
from urllib.request import urlretrieve
import pytz
import urllib.parse


# https://www.scrapingbee.com/blog/python-wget
def runcmd(cmd, verbose = False, *args, **kwargs):

    process = subprocess.Popen(
        cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        text = True,
        shell = True
    )
    std_out, std_err = process.communicate()
    if verbose:
        print(std_out.strip(), std_err)
    pass

def readtext(path):
    content = None
    f = open(path, 'r')
    content = f.read()
    f.close()
    return content

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
    if not os.path.exists(path):
       os.makedirs(path)

def download_wget(url, path):
    downloaded = 999
    runcmd("wget -O '" + path + "' " + url)
    if (os.path.exists(path)):
       if os.path.getsize(path) == 0:
          os.remove(path)
       else:
          downloaded = 200
    return downloaded

def download_request(url, path, proxy=None, useragent=None):
    downloaded = 999

    if proxy == None:
       response = requests.get(url)
    else:
       proxies = {
       'http': 'http://' + proxy,
       'https': 'http://' + proxy
       }
       headers = {
       "User-Agent": useragent
       }
       response = requests.get(url, proxies=proxies, headers=headers)

    downloaded = response.status_code
    if (response.ok and response.status_code == 200) or (response.status_code == 400 and not response.ok):
       with open(path, mode="wb") as f:
            f.write(response.content)

    return downloaded

def download(url, path, overwrite, querystringtracking, proxy=None, useragent=None, progress=False, verbose=False):
    # 1 = already downloaded
    # 10 = success request
    # 20 = success wget
    # 30 = success request using proxy and headers
    # 999 = failed
    downloaded = 999

    if url != None and url !='':
       if not querystringtracking:
          url = strip_querystring_url(url)
          path = strip_querystring_path(path)
       if path != None and path !='':
          path = sanitize(path)

          if (os.path.exists(path) and overwrite) or not os.path.exists(path):
             message = 'Downloading \'' + os.path.basename(path) + '\' ...'
             if verbose:
                print(message)

             downloaded = download_request(url, path)
             if downloaded == 200 or downloaded == 400:
                downloaded = 10
             else:
                downloaded = download_wget(url, path)
                if downloaded == 200:
                   downloaded = 20
                else:
                   downloaded = download_request(url, path, proxy, useragent)
                   if downloaded == 200 or downloaded == 400:
                      downloaded = 30

             if os.path.exists(path) and os.path.getsize(path) == 0:
                os.remove(path)

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
       try:
          json_text = json.loads(text)
       except Exception as e:
          json_text = "ERROR"

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

def format_date(date, format):
    formatted = date.strftime(format)
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

def to_timestamp(date):
    timestamp = date.timestamp()
    return timestamp

def timestamp_to_date(timestamp):
    date = datetime.fromtimestamp(timestamp)
    return date

def to_boolean(text):
    status = False
    if text.lower() == "true":
       status = True
    return status

def html_encode(string):
    safe_string = urllib.parse.quote(string)
    return safe_string

def samba_encode(string):
    safe_string = string
    safe_string = safe_string.replace("%22", "%C2%A8")
    safe_string = safe_string.replace("%2A", "%C2%A4")
    safe_string = safe_string.replace("%3A", "%C3%B7")
    safe_string = safe_string.replace("%3F", "%C2%BF")
    safe_string = safe_string.replace("%7C", "%C2%A6")
    return safe_string

def strip_querystring_url(path):
    path = path.rsplit('?', 1)[0]
    return path

def strip_querystring_path(path):
    path_split = path.rsplit('?', 1)
    path_stripped = path_split[0]
    if len(path_split) > 1:
       if path_split[1][0] == "/" or path_split[1][0] == " ":
          path_stripped = path
    return path_stripped
