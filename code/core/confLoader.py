# -*- coding: utf-8 -*-

import configparser
import random
import string
import logging


def load_conf(conf_file: str = 'configuration.conf'):
    """Load configuration from a file

    :param conf_file: the file to load
    :return: https_port, login, password, cookie_secret, debug, autoreload
    """
    # load configuration
    config = configparser.ConfigParser()
    config.read(conf_file)  # load configuration from 'configuration.conf' file
    # missing section ?
    if 'GENERAL' not in config:
        logging.error('Invalid configuration : Please verify [configuration.conf] contains a [GENERAL] section')
        raise ValueError('Please verify [configuration.conf] contains a [GENERAL] section')
    # missing a value ?
    if 'https_port' not in config['GENERAL'] or 'login' not in config['GENERAL'] \
            or 'password' not in config['GENERAL'] or 'cookie_secret' not in config['GENERAL']:
        logging.error('Invalid configuration : Please verify [GENERAL] section in [configuration.conf]')
        raise ValueError('Please verify [GENERAL] section in [configuration.conf]')
    # get configuration values
    https_port = config['GENERAL']['https_port']  # HTTPS port to bind
    login = config['GENERAL']['login']  # login for admin
    password = config['GENERAL']['password']  # password for admin
    cookie_secret = config['GENERAL']['cookie_secret']  # hash to create cookies
    if len(cookie_secret) < 1:  # empty cookie_secret value result in an automatic generation at app boot
        logging.info('No configuration : cookie_secret. Generating random secret.')
        cookie_secret = ''.join([random.choice(string.printable) for _ in range(24)])
    # load debug value
    debug = False  # default not in debug mode
    if 'debug' in config['GENERAL']:
        if isinstance(config['GENERAL']['debug'], bool):
            debug = config['GENERAL']['debug']
        else:
            logging.warning('Invalid configuration : debug. Continue without debug.')
    # load autoreload value
    autoreload = False  # default no app autoreload
    if 'autoreload' in config['GENERAL']:
        if isinstance(config['GENERAL']['autoreload'], bool):
            autoreload = config['GENERAL']['autoreload']
        else:
            logging.warning('Invalid configuration : autoreload. Continue without autoreload.')
    # load max attemps value
    max_attemps = 5  # default 5 attemps before blocking user
    if 'max_attemps' in config['GENERAL']:
        try:
            max_attemps = int(config['GENERAL']['max_attemps'])
        except ValueError:
            logging.warning('Invalid configuration : max_attemps. Continue with a default value of 5 attemps.')
    # load blocked duration value
    blocked_duration = 24  # default 1 day
    if 'blocked_duration' in config['GENERAL']:
        try:
            blocked_duration = int(config['GENERAL']['blocked_duration'])
        except ValueError:
            logging.warning('Invalid configuration : blocked_duration. Continue with a default duration of 24 hours.')
    # invalid configuration ?
    if not https_port or not login or not password or not cookie_secret \
            or int(https_port) < 1 or int(https_port) > 65535 \
            or len(login) < 1 or len(password) < 6 or len(cookie_secret) < 6 \
            or blocked_duration < 1 or max_attemps < 1:
        logging.error('Invalid configuration : Please verify configuration values in [configuration.conf]')
        raise ValueError('Please verify values in [configuration.conf]')
    return https_port, login, password, cookie_secret, debug, autoreload, max_attemps, blocked_duration
