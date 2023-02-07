from .db import DashboardDB, IssuesDB
import json

FILTER_KEYS = ['path', 'subtest', 'expected', 'actual', 'branch', 'build_url', 'pull_url']

def issues_mixin(path):
    issues = IssuesDB.readonly()
    return {'issues': issues.query(path)}

def tests(request):
    db = DashboardDB()
    result = []
    if 'group' in request.args:
        query = 'SELECT rowid, *, max("unexpected_count"), max("last_unexpected") FROM "test" WHERE "last_unexpected" IS NOT NULL GROUP BY "path" ORDER BY max("last_unexpected") DESC'
    else:
        query = 'SELECT rowid, * FROM "test" WHERE "last_unexpected" IS NOT NULL ORDER BY "last_unexpected" DESC'
    for test in db.con.execute(query).fetchall():
        result.append(dict(test) | issues_mixin(test['path']))
    return json.dumps(result)

def get_attempts(request):
    db = DashboardDB()
    result = []
    where = ''
    params = []
    for key in FILTER_KEYS:
        if key in request.args:
            where += f' AND "{key}" = ?'
            params.append(request.args[key])
    if 'since' in request.args:
        # use >= rather than > to allow repeated requests to pick up rows that
        # were inserted later in the same second than previous requests
        where += ' AND "time" >= ?'
        params.append(int(request.args['since']))
    for attempt in db.con.execute(f'SELECT rowid, * FROM "attempt" WHERE "actual" != "expected" {where} ORDER BY "time" DESC', params).fetchall():
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
