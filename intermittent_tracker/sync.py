from . import fs
from github3 import login
import json

with open(fs.CONFIG_PATH) as f:
    config = json.loads(f.read())

gh = login(token=config['github_token'])

issues = gh.issues_on(username='servo',
                      repository='servo',
                      labels='I-intermittent')

intermittents = []
for issue in issues:
    if 'C-disabled' in map(lambda l: l.as_dict()['name'], issue.labels()):
        continue

    issue = issue.as_dict()
    reduced = {
        'title': issue['title'],
        'number': issue['number'],
    }
    intermittents += [reduced]

print(json.dumps(intermittents))
