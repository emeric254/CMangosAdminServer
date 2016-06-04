# -*- coding: utf-8 -*-

import configparser
import random
import string
import logging


def load_web_server_conf(conf_file: str = 'configuration.conf'):
    """Load configuration from a file

    :param conf_file: the file to load
    :return: https_port, login, password, cookie_secret, debug, autoreload
    """
    config = configparser.ConfigParser()
    config.read(conf_file)  # load configuration from 'configuration.conf' file
    # missing section ?
    if 'WEB_SERVER' not in config:
        logging.error('Invalid configuration : Please verify [configuration.conf] contains a [WEB_SERVER] section')
        raise ValueError('Please verify [configuration.conf] contains a [WEB_SERVER] section')
    confs = config['WEB_SERVER']
    # missing a value ?
    if 'https_port' not in confs or 'login' not in confs \
            or 'password' not in confs or 'cookie_secret' not in confs:
        logging.error('Invalid configuration : Please verify [WEB_SERVER] section in [configuration.conf]')
        raise ValueError('Please verify [WEB_SERVER] section in [configuration.conf]')
    # get main configuration values
    https_port = confs['https_port']  # HTTPS port to bind
    login = confs['login']  # login for admin
    password = confs['password']  # password for admin
    cookie_secret = confs['cookie_secret']  # hash to create cookies
    if len(cookie_secret) < 1:  # empty cookie_secret value result in an automatic generation at app boot
        logging.info('No configuration : cookie_secret. Generating random secret.')
        cookie_secret = ''.join([random.choice(string.printable) for _ in range(24)])
    # load debug value
    debug = False  # default not in debug mode
    if 'debug' in confs:
        if confs['debug'] is '1':
            logging.warning('Debug mode activated.')
            debug = True
        else:
            logging.info('Debug mode not activated.')
    # load autoreload value
    autoreload = False  # default no app autoreload
    if 'autoreload' in confs:
        if confs['autoreload'] is '1':
            logging.warning('Autoreload mode activated.')
            autoreload = False
        else:
            logging.info('Autoreload mode not activated.')
    # load max attemps value
    max_attemps = 5  # default 5 attemps before blocking user
    if 'max_attemps' in confs:
        try:
            max_attemps = int(confs['max_attemps'])
        except ValueError:
            logging.warning('Invalid configuration : max_attemps. Continue with a default value of 5 attemps.')
    # load blocked duration value
    blocked_duration = 24  # default 1 day
    if 'blocked_duration' in confs:
        try:
            blocked_duration = int(confs['blocked_duration'])
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
