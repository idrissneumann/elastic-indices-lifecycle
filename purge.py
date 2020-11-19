import json

from time import sleep
from elasticsearch import Elasticsearch
from datetime import datetime
import pycurl
import re

with open('purge_conf.json') as json_file:
    conf = json.load(json_file)
    ES_HOSTS = conf['elastic_hosts']
    ES_PORT = conf['elastic_port']
    ES_SCHEME = conf['elastic_scheme']
    WAIT_TIME = conf['wait_time']
    INDEX_PREFIXES = conf['index_prefixes']
    INDEX_SUFFIXES = conf['index_suffixes']
    RETENTION = conf['retention']
    ES_USER = conf['elastic_username']
    ES_PASS = conf['elastic_password']
    SLACK_TRIGGER = conf['should_slack']
    SLACK_URL = conf['slack_url']
    SLACK_USERNAME = conf['slack_username']
    SLACK_CHANNEL = conf['slack_channel']
    SLACK_EMOJI = conf['slack_emoji']
    LOG_LEVEL = conf['log_level']

es = Elasticsearch(ES_HOSTS, http_auth=(ES_USER, ES_PASS), scheme = ES_SCHEME, port = ES_PORT)

def slack_message( message ):
    if SLACK_TRIGGER == 'on':
        c = pycurl.Curl()
        c.setopt(pycurl.URL, SLACK_URL)
        c.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])
        c.setopt(pycurl.POST, 1)
        data = json.dumps({"text": message, "username": SLACK_USERNAME, "channel": SLACK_CHANNEL, "icon_emoji": SLACK_EMOJI })
        c.setopt(pycurl.POSTFIELDS, data)
        c.perform()

def check_log_level ( log_level ):
    if LOG_LEVEL == "debug":
        return True
    else:
        return log_level != "debug"

def quiet_log_msg ( log_level, message ):
    if check_log_level(log_level):
        print (message)

def log_msg( log_level, message ):
    if check_log_level(log_level):
        quiet_log_msg (log_level, message)
        slack_message(message)

def perform_delete( indice, creation_date ):
    d = (datetime.now() - creation_date).days
    if d > RETENTION:
        log_msg("info", "Removing indice i={} because d={} > r={}".format(indice, d, RETENTION))
        es.indices.delete(index=indice, ignore=[400, 404])

while True:
    log_msg("info", "Check if indices matching with prefixes = {} and suffixes = {}".format(INDEX_PREFIXES, INDEX_SUFFIXES))
    for indice in es.indices.get('*'):
        if INDEX_PREFIXES:
            for prefix in INDEX_PREFIXES:
                if indice.startswith(prefix):
                    creation_date =  datetime.strptime(indice, "{}-%Y%m%d".format(prefix))
                    quiet_log_msg("debug", "Check indice {} with creation_date : {} because of prefix {}".format(indice, creation_date, prefix))
                    perform_delete(indice, creation_date)

        if INDEX_SUFFIXES:
            for suffix in INDEX_SUFFIXES:
                capture = re.findall("^.*{}-([0-9]+)$".format(suffix), indice)
                if capture:
                    creation_date =  datetime.strptime(capture[0], "%Y%m%d")
                    quiet_log_msg("debug", "Check indice {} with creation_date : {} because of suffix {}".format(indice, creation_date, suffix))
                    perform_delete(indice, creation_date)
    sleep(WAIT_TIME)