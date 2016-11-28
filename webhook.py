#!/usr/bin/env python

from __future__ import absolute_import, print_function

import cgi
import cgitb
try:
    import simplejson as json
except:
    import json

import handlers
from db import AutoWriteDB

if __name__ == "__main__":
    print("Content-Type: text/html;charset=utf-8")
    print()

    cgitb.enable()

    post = cgi.FieldStorage()
    payload_raw = post.getfirst("payload", '')
    payload = json.loads(payload_raw)

    action = payload['action']
    if action not in ['labeled', 'unlabeled', 'edited', 'closed', 'reopened']:
        return

    db = AutoWriteDB('intermittents.json')

    issue = payload['issue']
    if action == 'labeled':
        handlers.on_label_added(db, payload['label']['name'],
                                issue['title'], issue['number'], payload['state'])
    elif action == 'unlabled':
        handlers.on_label_removed(db, payload['label']['name'],
                                  issue['title'], issue['number'], payload['state'])
    elif action == 'closed':
        handlers.on_issue_closed(db, issue['number'])
    elif action == 'reopened':
        handlers.on_issue_closed(db, issue['name'], issue['number'],
                                 map(lambda l: l['name'], issue['labels']))
    elif action == 'edited':
        handlers.on_issue_updated(db, issue['name'], issue['number'],
                                  map(lambda l: l['name'], issue['labels'],
                                  payload['state']))
    else:
        raise "Unexpected action encounted: %s" % action
