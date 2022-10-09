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

def log(isErrorLogger, isDebug, message):
    if isErrorLogger:
       config.logger_error.error(message)
    else:
       if isDebug:
          config.logger_app.debug(message)
          logger.debug(message)
       else:
          config.logger_app.info(message)
