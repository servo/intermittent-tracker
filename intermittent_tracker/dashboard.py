from .db import DashboardDB, IssuesDB
import json

def issues_mixin(path):
    issues = IssuesDB.readonly()
    return {'issues': issues.query(path)}

def tests(request):
    db = DashboardDB.connect()
    result = []
    for test in db.con.execute('SELECT * FROM "test" WHERE "last_unexpected" IS NOT NULL ORDER BY "last_unexpected" DESC').fetchall():
        result.append(dict(test) | issues_mixin(test['path']))
    return json.dumps(result)

def test(request):
    db = DashboardDB.connect()
    result = {'unexpected': []} | issues_mixin(request.args['path'])
    where = (request.args['path'], request.args['subtest'])
    for attempt in db.con.execute('SELECT * FROM "attempt" WHERE "path" = ? AND "subtest" = ? AND "actual" != "expected" ORDER BY "time" DESC', where).fetchall():
        result['unexpected'].append(dict(attempt))
    return json.dumps(result)

def post_attempts(request):
    db = DashboardDB.connect()
    db.insert_attempts(*request.json)
    return ('', 204)
