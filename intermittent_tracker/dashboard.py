from .db import DashboardDB, IssuesDB
import json

def issues_mixin(path):
    issues = IssuesDB.readonly()
    result = issues.query(path)
    return {'issues': result} if result else {}

def tests(request):
    db = DashboardDB()
    result = []
    if 'group' in request.args:
        query = 'SELECT *, max("unexpected_count"), max("last_unexpected") FROM "test" WHERE "last_unexpected" IS NOT NULL GROUP BY "path" ORDER BY max("last_unexpected") DESC'
    else:
        query = 'SELECT * FROM "test" WHERE "last_unexpected" IS NOT NULL ORDER BY "last_unexpected" DESC'
    for test in db.con.execute(query).fetchall():
        result.append({**test, **issues_mixin(test['path'])})
    return json.dumps(result)

def get_attempts(request):
    db = DashboardDB()
    filters = request.args.to_dict()
    since = filters.pop('since', None)
    since = int(since) if since is not None else None
    return json.dumps(db.select_attempts(since=since, **filters))

def post_attempts(request):
    db = DashboardDB()
    attempts = request.json['attempts']
    branch = request.json['branch']
    build_url = request.json['build_url']
    pull_url = request.json['pull_url']
    db.insert_attempts(attempts, branch=branch, build_url=build_url, pull_url=pull_url)
    return query(request)

def query(request):
    result = {'known': [], 'unknown': []}
    attempts = request.json['attempts']
    for attempt in attempts:
        test = {'path': attempt['path'], 'subtest': attempt.get('subtest')}
        issues = issues_mixin(attempt['path'])
        if issues:
            result['known'].append({**test, **issues})
        else:
            result['unknown'].append(test)
    return json.dumps(result)

def most_flaky(limit=100):
    db = DashboardDB()
    result = []
    query = f'SELECT path, SUM(unexpected_count) AS total_unexpected_count FROM "test" GROUP BY path ORDER BY total_unexpected_count DESC LIMIT {limit}'
    query_result = db.con.execute(query).fetchall()
    for row in query_result:
        test = {
            'path': row['path'],
            'total_unexpected_count': row['total_unexpected_count']
        }
        issues = issues_mixin(test['path'])
        test['issues'] = issues
        result.append(test)
    return result