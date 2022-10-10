#!/usr/bin/env python3

import sys
import os
import logging

import config
import generalfunctions

def configure(filename_app, filename_error):
    formatter_app = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler = generalfunctions.log_handler_file(filename_app)
    handler.setFormatter(formatter_app)
    config.logger_app.setLevel(logging.INFO)
    config.logger_app.addHandler(handler)

    formatter_error = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler = generalfunctions.log_handler_file(filename_error)
    handler.setFormatter(formatter_error)
    config.logger_error.setLevel(logging.DEBUG)
    config.logger_error.addHandler(handler)

def log(isErrorLogger, level, message):
    if isErrorLogger:
       if level == 'WARN':
          config.logger_error.warn(message)
       if level == 'ERROR':
          config.logger_error.error(message)
       if level == 'DEBUG':
          config.logger_error.debug(message)
    else:
       if level == 'INFO':
          config.logger_app.info(message)
       if level == 'WARN':
          config.logger_app.warn(message)
