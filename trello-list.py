# -*- coding: utf-8 -*-
import trello

import os
import re
import datetime
import pytz
import time

client = trello.TrelloClient(
    api_key=os.environ['TRELLO_API_KEY'],
    api_secret=os.environ['TRELLO_API_SECRET'],
    token=os.environ['TRELLO_TOKEN'],
    token_secret=os.environ['TRELLO_SECRET'],
)
dci_board = client.get_board('0eMozAiR')

def get_id_from_url(url):
    m = re.search('trello.com/c/(\w+)/.*', url, re.IGNORECASE)
    return m.group(1)


def list_epics_from_card(c):
    return re.findall('Link: (\S+)', c.desc, re.IGNORECASE)


def update_epic_list(epics):
    epic_list = dci_board.get_list('59034ed48cfb968afdb0fcc5')
    current_epics = epic_list.list_cards()
    for epic in epics:
        ce = client.get_card(get_id_from_url(epic))
        # if the epic has itself relationship with some other epics
        card_epics = re.findall('Link: (\S+)', ce.desc, re.IGNORECASE)
        description = 'update by DCI Epic bot:\n\n'
        for s in epics[epic]:
            icon = ''
            if 'Done' in s.trello_list.name:
                icon = ':heavy_check_mark:'
            elif 'Review' in s.trello_list.name:
                icon = ':microscope:'
            elif 'Stalling' in s.trello_list.name:
                icon = ':skull:'
            elif 'Doing' in s.trello_list.name:
                icon = ':construction_worker:'
            description += '- '
            description += icon
            description += s.url
            description += '\n'
        for e in set(card_epics):
            description += 'DCI-Epic: '
            description += e
            description += '\n'
        ce.set_description(description)


def refresh():
    epics = {}
    for l in dci_board.all_lists():
        if l.closed:
            continue
        trello_list = dci_board.get_list(l.id)
        for c in trello_list.list_cards():
            if u'[investigation]' in c.name:
                new_name = c.name.decode().replace(u'[investigation]', u'🔍')
                c.set_name(new_name)
            if u'[article]' in c.name:
                new_name = c.name.decode().replace(u'[article]', u'📖')
                c.set_name(new_name)
            c.list = l
            for epic in list_epics_from_card(c):
                epic = epic.rstrip()
                if epic not in epics:
                    epics[epic] = []
                epics[epic].append(c)
    update_epic_list(epics)


last_run = datetime.datetime.utcfromtimestamp(0)
while True:
    try:
        if pytz.utc.localize(last_run) < dci_board.get_last_activity():
            last_run = datetime.datetime.utcnow()
            refresh()
    except trello.exceptions.ResourceUnavailable:
        pass
    time.sleep(600)
