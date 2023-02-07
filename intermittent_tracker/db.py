import json
import sqlite3
import time
from itertools import count

class IssuesDB:
    @staticmethod
    def readonly(filename='data/issues.json'):
        with open(filename) as f:
            return IssuesDB(json.loads(f.read()))

    @staticmethod
    def autowrite(filename='data/issues.json'):
        return AutoWriteIssuesDB(filename)

    def __init__(self, db):
        self.data = db

    def query(self, name):
        # In Python 3 filter() is lazy, so we build an array right here so that it can be jsonified
        return [x for x in filter(lambda i: name in i['title'], self.data)]

    def add(self, name, number):
        for i in self.data:
            if i['number'] == number:
                return
        self.data.extend([{'title': name, 'number': number}])

    def remove(self, number):
        for idx, i in enumerate(self.data):
            if i['number'] == number:
                self.data.pop(idx)
                return


class AutoWriteIssuesDB(IssuesDB):
    def __init__(self, filename):
        self.filename = filename
        with open(filename) as f:
            super().__init__(json.loads(f.read()))

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, etrace):
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.data))


class DashboardDB:
    migrations = []
    expected_version = 0
    for version in count(1):
        try:
            with open(f'schema/dashboard.{version}.sql') as f:
                migrations.append(f.read())
                expected_version = version
        except FileNotFoundError:
            break

    @staticmethod
    def migrate(filename='data/dashboard.sqlite'):
        con = connect(filename)
        version = 0
        try:
            version = con.execute('SELECT * FROM meta').fetchone()['version']
        except sqlite3.OperationalError as e:
            if not str(e).startswith('no such table: '):
                raise
        for migration in DashboardDB.migrations[version:]:
            con.executescript(f'BEGIN; {migration}; COMMIT; VACUUM')

    def __init__(self, filename='data/dashboard.sqlite'):
        self.con = connect(filename)
        if filename == ':memory:':
            for migration in DashboardDB.migrations:
                self.con.executescript(f'BEGIN; {migration}; COMMIT; VACUUM')
        try:
            version = self.con.execute('SELECT * FROM meta').fetchone()['version']
            assert version == DashboardDB.expected_version
        except sqlite3.OperationalError as e:
            if str(e).startswith('no such table: '):
                raise Exception('database seems to be empty; did you call migrate()?')
            raise
        except AssertionError:
            raise Exception('database out of date; did you call migrate()?')

    def __enter__(self):
        self.con.__enter__()

    def __exit__(self):
        self.con.__exit__()

    def insert_attempt(self, *, submission, path, subtest=None, expected, actual, time,
                       message=None, stack=None):
        self.con.execute('SAVEPOINT "insert_attempt"')
        if actual != expected:
            self.con.execute("""
                INSERT INTO "test" VALUES (NULL,?,?,1,?) ON CONFLICT DO UPDATE SET
                    "unexpected_count" = "unexpected_count" + 1
                    , "last_unexpected" = ?
            """, (path, subtest, time, time))
        else:
            self.con.execute('INSERT INTO "test" VALUES (NULL,?,?,0,NULL) ON CONFLICT DO NOTHING', (path, subtest))
        # SELECT query needed for test_id because Cursor.lastrowid is stale
        # (0 or lastrowid from a previous Cursor) when ON CONFLICT is taken
        test = self.con.execute('SELECT * FROM "test" WHERE "path" = ? AND "subtest" IS ?', (path, subtest)).fetchone()
        self.con.execute('INSERT INTO "attempt" VALUES (NULL,?,?,?,?,?,?,?)',
            (test['test_id'], expected, actual, time, message, stack, submission))
        self.con.execute('RELEASE "insert_attempt"')

    def insert_attempts(self, attempts, *, branch=None, build_url=None, pull_url=None):
        self.con.execute('SAVEPOINT "insert_attempts"')
        # grab lastrowid before the loop, because it will get clobbered
        submission = self.con.execute('INSERT INTO "submission" VALUES (NULL,?,?,?,?)', (now(), branch, build_url, pull_url)).lastrowid
        for attempt in attempts:
            self.insert_attempt(submission=submission, **attempt)
        self.con.execute('RELEASE "insert_attempts"')


def now():
    return int(time.time())


def connect(filename):
    con = sqlite3.connect(filename)
    con.row_factory = sqlite3.Row

    # generally faster, but database must be on a local filesystem
    con.execute('PRAGMA journal_mode=wal')

    return con


# python3 -im intermittent_tracker.db
if __name__ == '__main__':
    DashboardDB.migrate()
    d = DashboardDB()
