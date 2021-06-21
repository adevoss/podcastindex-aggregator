#!/usr/bin/env python3

import csv
import os
import requests
import json
import pathlib
from datetime import datetime


def log(path, message):
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

def download(url, path, log_path, overwrite):
    downloaded = False
    try:
        if url != None:
            if (os.path.isfile(path) and overwrite) or not os.path.isfile(path):
                message = 'Downloading \'' + url + '\''
                print(message)
                log(log_path, message)

                r = requests.get(url)
                with open(path, 'wb') as outfile:
                    outfile.write(r.content)
                downloaded = True

    except Exception as e:
        log(log_path, str(e))
        print(e)

    return downloaded

def write_file(path, text):
    with open(path, "w") as outfile: 
        outfile.write(text)

def read_json(path, log_path):
    try:
       json_text = ''
       with open(path, 'r', encoding="utf-8-sig") as openfile: 
            text = openfile.read()
            openfile.close()

       # strip BOM character
       json_text = text.lstrip('\ufeff')
       json_text = json.loads(text)

    except Exception as e:
        log(log_path, str(e))
        print(e)

    return json_text

def file_extension(path):
    extension = pathlib.Path(path).suffix
    return extension

def file_name_noextension(path):
    name = os.path.splitext(path)[0]
    return name

def format_dateYYYMMDDHHMM(date):
    format = "%Y%m%d%H%M"
    formatted = date.strftime(format)
    return formatted

def now():
    date = datetime.now()
    return date

def date_epoch(date):
    epoch = date.timestamp()
    return epoch

