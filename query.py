#!/usr/bin/env python

from __future__ import absolute_import, print_function

import cgi
import cgitb
try:
    import simplejson as json
except:
    import json

import handlers
from db import IntermittentsDB

def query(name):
    with open('intermittents.json') as f:
        db = IntermittentsDB(json.loads(f.read()))
    return db.query(name)

if __name__ == "__main__":
    print("Content-Type: application/json;charset=utf-8")
    print()

    cgitb.enable()

    post = cgi.FieldStorage()
    name = post.getfirst("name", None)
    if name:
        print(json.dumps(query(name)))
    else:
        print('null')
