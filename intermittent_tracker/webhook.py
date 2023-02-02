#!/usr/bin/env python

from __future__ import absolute_import, print_function

import cgi
import cgitb
try:
    import simplejson as json
except:
    import json

from . import handlers
from .db import AutoWriteIssuesDB

def handler(payload_raw):
    payload = json.loads(payload_raw)
    action = payload['action']
    if action not in ['labeled', 'unlabeled', 'edited', 'closed', 'reopened']:
        return

    with AutoWriteIssuesDB('data/issues.json') as db:
        issue = payload['issue']
        if action == 'labeled':
            handlers.on_label_added(db, payload['label']['name'],
                                    issue['title'], issue['number'], issue['state'])
        elif action == 'unlabeled':
            handlers.on_label_removed(db, payload['label']['name'],
                                      issue['title'], issue['number'], issue['state'])
        elif action == 'closed':
            handlers.on_issue_closed(db, issue['number'])
        elif action == 'reopened':
            handlers.on_issue_reopened(db, issue['title'], issue['number'],
                                     map(lambda l: l['name'], issue['labels']))
        elif action == 'edited':
            handlers.on_issue_updated(db, issue['title'], issue['number'],
                                      map(lambda l: l['name'], issue['labels']),
                                          issue['state'])
        else:
            raise "Unexpected action encounted: %s" % action

if __name__ == "__main__":
    print("Content-Type: text/html;charset=utf-8")
    print()

    cgitb.enable()

    post = cgi.FieldStorage()
    payload = post.getfirst("payload", '')
    handler(payload)
