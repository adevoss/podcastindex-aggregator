#!/usr/bin/env python3

import sys
import os
import json

def read():
    global file
    with open("/etc/podcastindex/config.json") as config_file:
         file = json.load(config_file)

