from .db import DashboardDB, IssuesDB
import json

def issues_mixin(path):
    issues = IssuesDB.readonly()
    return {'issues': issues.query(path)}

def tests(request):
    db = DashboardDB()
    result = []
    for test in db.con.execute('SELECT *, rowid FROM "test" WHERE "last_unexpected" IS NOT NULL ORDER BY "last_unexpected" DESC').fetchall():
        result.append(dict(test) | issues_mixin(test['path']))
    return json.dumps(result)

def test(request):
    db = DashboardDB()
    result = {'unexpected': []} | issues_mixin(request.args['path'])
    where = (request.args['path'], request.args['subtest'])
    for attempt in db.con.execute('SELECT *, rowid FROM "attempt" WHERE "path" = ? AND "subtest" = ? AND "actual" != "expected" ORDER BY "time" DESC', where).fetchall():
        result['unexpected'].append(dict(attempt))
    return json.dumps(result)

def post_attempts(request):
    db = DashboardDB()
    db.insert_attempts(*request.json)
    issues = IssuesDB.readonly()
    result = [attempt for attempt in request.json if not issues.query(attempt['path'])]
    return json.dumps(result)
