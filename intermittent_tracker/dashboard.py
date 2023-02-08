from .db import DashboardDB, IssuesDB
import json
import time

FILTER_KEYS = ['path', 'subtest', 'expected', 'actual', 'branch', 'build_url', 'pull_url']

def issues_mixin(path):
    issues = IssuesDB.readonly()
    return {'issues': issues.query(path)}

def tests(request):
    db = DashboardDB()
    result = []
    if 'group' in request.args:
        query = 'SELECT *, max("unexpected_count"), max("last_unexpected") FROM "test" WHERE "last_unexpected" IS NOT NULL GROUP BY "path" ORDER BY max("last_unexpected") DESC'
    else:
        query = 'SELECT * FROM "test" WHERE "last_unexpected" IS NOT NULL ORDER BY "last_unexpected" DESC'
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
        where += ' AND "attempt_id" > ?'
        params.append(int(request.args['since']))
    start = time.monotonic_ns()
    for attempt in db.con.execute(f'SELECT "path", "subtest", "attempt".*, "branch", "build_url", "pull_url" FROM "attempt", "test", "submission" WHERE "test" = "test_id" AND "submission" = "submission_id" AND "actual" != "expected" {where} ORDER BY "attempt_id"', params).fetchall():
        result.append(dict(attempt))
    print(f'debug: GET /dashboard/attempts query took {time.monotonic_ns() - start} ns')
    return json.dumps(result)

def post_attempts(request):
    db = DashboardDB()
    attempts = request.json['attempts']
    branch = request.json['branch']
    build_url = request.json['build_url']
    pull_url = request.json['pull_url']
    db.insert_attempts(attempts, branch=branch, build_url=build_url, pull_url=pull_url)
    return query(request)

def query(request):
    issues_db = IssuesDB.readonly()
    result = {'known': [], 'unknown': []}
    attempts = request.json['attempts']
    for attempt in attempts:
        test = {'path': attempt['path'], 'subtest': attempt.get('subtest')}
        issues = issues_db.query(attempt['path'])
        if issues:
            result['known'].append(test | {'issues': issues})
        else:
            result['unknown'].append(test)
    return json.dumps(result)
