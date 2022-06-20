#!/usr/bin/env python3

import configuration
import generalfunctions

from datetime import date
import hashlib
import json
import requests
import time

# uncomment these to make debugging easier.
# print ('api key: ' + api_key);
# print ('api secret: ' + api_secret);
# print ('query: ' + query);
# print ('url: ' + url);



# the api follows the Amazon style authentication
# see https://docs.aws.amazon.com/AmazonS3/latest/dev/S3_Authentication2.html

def request_header():
    # setup some basic vars for the search api. 
    # for more information, see https://api.podcastindex.org/developer_docs
    global config
    api_key = configuration.config["podcastindex"]["key"]
    api_secret = configuration.config["podcastindex"]["secret"]

    # we'll need the unix time
    epoch_time = int(time.time())

    # our hash here is the api key + secret + time 
    data_to_hash = api_key + api_secret + str(epoch_time)
    # which is then sha-1'd
    sha_1 = hashlib.sha1(data_to_hash.encode()).hexdigest()

    # now we build our request headers
    headers = {
        'X-Auth-Date': str(epoch_time),
        'X-Auth-Key': api_key,
        'Authorization': sha_1,
        'User-Agent': 'postcasting-index-python-cli'
    }
    return headers

def request(url, log_path):
    try:
       result = None
       # perform the actual post request
       r = requests.post(url, headers=request_header())

       # dump the contents (in a prettified json-format)
       result = json.loads(r.text)

    except Exception as e:
        message = 'Podcast Index API call: ' + str(e)
        generalfunctions.log(log_path, message, True, False)
        print(message)

    return result

