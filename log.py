#!/usr/bin/env python3

import sys
import os
import logging

import generalfunctions

def configure(filename_app, filename_error):
    global logger_app
    global logger_error

    logger_app = logging.getLogger("app")
    logger_error = logging.getLogger("error")
    logger_app.setLevel(logging.INFO)
    logger_app.setLevel(logging.DEBUG)

    formatter_app = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fileHandler_app = logging.FileHandler(filename_app, mode='a', encoding='utf-8', delay=True)
    fileHandler_app.setFormatter(formatter_app)

    formatter_error = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fileHandler_error = logging.FileHandler(filename_error, mode='a', encoding='utf-8', delay=True)
    fileHandler_error.setFormatter(formatter_error)

    logger_app.addHandler(fileHandler_app)
    logger_error.addHandler(fileHandler_error)


def log(isErrorLogger, level, message):
    if isErrorLogger:
       if level == 'DEBUG':
          logger_error.debug(message)
       if level == 'INFO':
          logger_error.info(message)
       if level == 'WARN':
          logger_error.warn(message)
       if level == 'ERROR':
          logger_error.error(message)
       if level == 'CRITICAL':
          logger_error.critical(message)
    else:
       if level == 'DEBUG':
          logger_app.debug(message)
       if level == 'INFO':
          logger_app.info(message)
       if level == 'WARN':
          logger_app.warn(message)
       if level == 'ERROR':
          logger_app.error(message)
       if level == 'CRITICAL':
          logger_app.critical(message)
