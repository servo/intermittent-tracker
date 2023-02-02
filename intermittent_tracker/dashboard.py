from .db import DashboardDB, IssuesDB
import json

def issues_mixin(path):
    issues = IssuesDB.readonly()
    return {'issues': issues.query(path)}

def tests(request):
    db = DashboardDB()
    result = []
    if 'group' in request.args:
        query = 'SELECT *, rowid, max("unexpected_count"), max("last_unexpected") FROM "test" WHERE "last_unexpected" IS NOT NULL GROUP BY "path" ORDER BY max("last_unexpected") DESC'
    else:
        query = 'SELECT *, rowid FROM "test" WHERE "last_unexpected" IS NOT NULL ORDER BY "last_unexpected" DESC'
    for test in db.con.execute(query).fetchall():
        result.append(dict(test) | issues_mixin(test['path']))
    return json.dumps(result)

def get_attempts(request):
    db = DashboardDB()
    result = []
    where = ''
    params = []
    if 'path' in request.args:
        where += ' AND "path" = ?'
        params.append(request.args['path'])
    if 'subtest' in request.args:
        where += ' AND "subtest" = ?'
        params.append(request.args['subtest'])
    if 'branch' in request.args:
        where += ' AND "branch" = ?'
        params.append(request.args['branch'])
    if 'build_url' in request.args:
        where += ' AND "build_url" = ?'
        params.append(request.args['build_url'])
    if 'pull_url' in request.args:
        where += ' AND "pull_url" = ?'
        params.append(request.args['pull_url'])
    if 'since' in request.args:
        # use >= rather than > to allow repeated requests to pick up rows that
        # were inserted later in the same second than previous requests
        where += ' AND "time" >= ?'
        params.append(int(request.args['since']))
    for attempt in db.con.execute(f'SELECT *, rowid FROM "attempt" WHERE "actual" != "expected" {where} ORDER BY "time" DESC', params).fetchall():
        result.append(dict(attempt))
    return json.dumps(result)

def post_attempts(request):
    db = DashboardDB()
    db.insert_attempts(*request.json)
    return query(request)

def query(request):
    issues_db = IssuesDB.readonly()
    result = {'known': [], 'unknown': []}
    for attempt in request.json:
        test = {'path': attempt['path'], 'subtest': attempt.get('subtest')}
        issues = issues_db.query(attempt['path'])
        if issues:
            result['known'].append(test | {'issues': issues})
        else:
            result['unknown'].append(test)
    return json.dumps(result)
