from . import fs
import json
import sqlite3
import time
from zlib import crc32
from itertools import count


FILTER_KEYS = ['path', 'subtest', 'expected', 'actual', 'branch', 'build_url', 'pull_url']


class IssuesDB:
    @staticmethod
    def readonly(filename=fs.ISSUES_JSON_PATH):
        with open(filename) as f:
            return IssuesDB(json.loads(f.read()))

    @staticmethod
    def autowrite(filename=fs.ISSUES_JSON_PATH):
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
            with open(f'{fs.SCHEMA_PATH}/dashboard.{version}.sql') as f:
                migrations.append(f.read())
                expected_version = version
        except FileNotFoundError:
            break

    @staticmethod
    def migrate(filename=fs.DASHBOARD_SQLITE_PATH):
        con = connect(filename)
        version = 0
        try:
            version = con.execute('SELECT * FROM meta').fetchone()['version']
        except sqlite3.OperationalError as e:
            if not str(e).startswith('no such table: '):
                raise
        for migration in DashboardDB.migrations[version:]:
            con.executescript(f'BEGIN; {migration}; COMMIT; VACUUM')

    def __init__(self, filename=fs.DASHBOARD_SQLITE_PATH):
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

    def select_attempts(self, *, since=None, **filters):
        result = []
        where = ''
        params = []
        if since is not None:
            where += ' AND "attempt_id" > ?'
            params.append(since)
        for key in FILTER_KEYS:
            if key in filters:
                where += f' AND "{key}" = ?'
                params.append(filters[key])
        start = time.monotonic_ns()
        for attempt in self.con.execute(f'SELECT "path", "subtest", "attempt".*, "message", "stack", "branch", "build_url", "pull_url" FROM "attempt", "test", "output", "submission" WHERE "test" = "test_id" AND "output" = "output_id" AND "submission" = "submission_id" AND "actual" != "expected" {where} ORDER BY "attempt_id"', params).fetchall():
            result.append(dict(attempt))
        print(f'debug: DashboardDB.select_attempts took {time.monotonic_ns() - start} ns')
        return result

    def insert_attempt(self, *, submission, path, subtest=None, expected, actual, time,
                       message=None, stack=None):
        self.con.execute('SAVEPOINT "insert_attempt"')
        if actual != expected:
            self.con.execute("""
                INSERT INTO "test" VALUES (NULL,?,?,1,?) ON CONFLICT DO UPDATE SET
                    "unexpected_count" = "unexpected_count" + 1
                    , "last_unexpected" = max("last_unexpected",?)
            """, (path, subtest, time, time))
        else:
            self.con.execute('INSERT INTO "test" VALUES (NULL,?,?,0,NULL) ON CONFLICT DO NOTHING', (path, subtest))

        # SELECT query needed for test_id because Cursor.lastrowid is stale
        # (0 or lastrowid from a previous Cursor) when ON CONFLICT is taken
        test = self.con.execute('SELECT * FROM "test" WHERE "path" = ? AND "subtest" IS ?', (path, subtest)).fetchone()
        test_id = test['test_id']

        message_hash = crc32(message.encode('utf-8')) if message is not None else 0
        stack_hash = crc32(stack.encode('utf-8')) if stack is not None else 0
        output = self.con.execute('SELECT * FROM "output" WHERE "message_hash" = ? AND "stack_hash" = ? AND "message" IS ? AND "stack" IS ?', (message_hash, stack_hash, message, stack)).fetchone()
        if output is not None:
            output_id = output['output_id']
        else:
            # if we can’t find a row by hashes, maybe there’s an unhashed row from before schema v2?
            output = self.con.execute('SELECT * FROM "output" WHERE "message_hash" IS NULL AND "stack_hash" IS NULL AND "message" IS ? AND "stack" IS ?', (message, stack)).fetchone()
            if output is not None:
                # update the unhashed row accordingly
                self.con.execute('UPDATE "output" SET "message_hash" = ?, "stack_hash" = ? WHERE "output_id" = ?', (message_hash, stack_hash, output['output_id']))
                output_id = output['output_id']
            else:
                # if we still can’t find a row, we need to insert one
                output_id = self.con.execute('INSERT INTO "output" VALUES (NULL,?,?,?,?)', (message, stack, message_hash, stack_hash)).lastrowid

        self.con.execute('INSERT INTO "attempt" VALUES (NULL,?,?,?,?,?,?)',
            (test_id, expected, actual, time, output_id, submission))
        self.con.execute('RELEASE "insert_attempt"')

    def insert_attempts(self, attempts, *, branch=None, build_url=None, pull_url=None, time_for_testing=None):
        submission_time = time_for_testing if time_for_testing is not None else now()
        start = time.monotonic_ns()
        self.con.execute('SAVEPOINT "insert_attempts"')
        # grab lastrowid before the loop, because it will get clobbered
        submission = self.con.execute('INSERT INTO "submission" VALUES (NULL,?,?,?,?)', (submission_time, branch, build_url, pull_url)).lastrowid
        for attempt in attempts:
            self.insert_attempt(submission=submission, **attempt)
        self.con.execute('RELEASE "insert_attempts"')
        print(f'debug: DashboardDB.insert_attempts took {time.monotonic_ns() - start} ns')


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
    fs.mkdir_data()
    DashboardDB.migrate()
    d = DashboardDB()
