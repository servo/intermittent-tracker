import json
import sqlite3
import time

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


class AutoWriteDB:
    def __init__(self, filename):
        self.filename = filename
        with open(filename) as f:
            super().__init__(json.loads(f.read()))

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, etrace):
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.data))


class AutoWriteIssuesDB(AutoWriteDB, IssuesDB):
    def __init__(self, filename):
        super().__init__(filename)


class DashboardDB:
    @staticmethod
    def connect():
        return DashboardDB('data/dashboard.sqlite')

    def __init__(self, filename):
        self.version = 0  # schema version (0 = empty database)
        self.con = sqlite3.connect(filename)
        self.con.row_factory = sqlite3.Row

        # generally faster, but database must be on a local filesystem
        self.con.execute("PRAGMA journal_mode=wal")

        # schema version (susceptible to toctou)
        try:
            meta = self.con.execute("SELECT * FROM meta").fetchone()
            self.version = meta['version']
        except sqlite3.OperationalError as e:
            if not str(e).startswith('no such table: '):
                raise

        # schema migrations
        if self.version < 1:
            self.con.execute("BEGIN")
            self.con.execute("""
                CREATE TABLE "meta" (
                "version" INTEGER NOT NULL
                )
            """)
            self.con.execute("""
                INSERT INTO "meta" VALUES (1)
            """)
            self.con.execute("""
                CREATE TABLE "test" (
                "path" TEXT NOT NULL                        -- test name
                , "subtest" TEXT
                , "unexpected_count" INTEGER NOT NULL
                , "last_unexpected" INTEGER                 -- unix time
                , PRIMARY KEY ("path", "subtest")
                )
            """)
            self.con.execute("""
                CREATE TABLE "attempt" (
                "path" TEXT NOT NULL                        -- test name
                , "subtest" TEXT
                , "expected" TEXT NOT NULL                  -- status e.g. PASS
                , "actual" TEXT NOT NULL                    -- status e.g. FAIL
                , "time" INTEGER NOT NULL                   -- unix time
                , "message" TEXT DEFAULT NULL               -- test output
                , "stack" TEXT DEFAULT NULL
                , "branch" TEXT DEFAULT NULL                -- e.g. auto, try
                , "build_url" TEXT DEFAULT NULL             -- e.g. https://github.com/servo/servo/actions/runs/4030556190/jobs/6929482570
                , "pull_url" TEXT DEFAULT NULL              -- e.g. https://github.com/servo/servo/pull/29306
                , FOREIGN KEY ("path", "subtest") REFERENCES "test"
                )
            """)
            self.con.execute("""
                CREATE INDEX "attempt.test" ON "attempt" ("path", "subtest")
            """)
            self.con.execute("""
                CREATE INDEX "attempt.build" ON "attempt" ("build_url")
            """)
            self.con.execute("""
                CREATE INDEX "attempt.pull" ON "attempt" ("pull_url")
            """)
            self.con.execute("""
                CREATE TRIGGER "test.count_unexpected"
                INSERT ON "attempt"
                BEGIN
                    INSERT INTO "test" VALUES (
                        new."path", new."subtest"
                        , CASE WHEN new."actual" != new."expected" THEN 1 ELSE 0 END
                        , CASE WHEN new."actual" != new."expected" THEN new."time" ELSE NULL END
                    ) ON CONFLICT DO UPDATE SET
                        "unexpected_count" = "unexpected_count" + 1
                        , "last_unexpected" = new."time"
                        WHERE new."actual" != new."expected";
                END
            """)
            self.con.execute("COMMIT")

    def __enter__(self):
        self.con.__enter__()

    def __exit__(self):
        self.con.__exit__()

    def insert_attempt(self, *, path, subtest=None, expected, actual, time=None,
                       message=None, stack=None, branch=None, build_url=None, pull_url=None):
        if time is None:
            time = now()
        self.con.execute('INSERT INTO "attempt" VALUES (?,?,?,?,?,?,?,?,?,?)',
            (path, subtest, expected, actual, time, message, stack, branch, build_url, pull_url))

    def insert_attempts(self, *attempts):
        for attempt in attempts:
            self.insert_attempt(**attempt)


def now():
    return int(time.time())


# python3 -im intermittent_tracker.db
if __name__ == '__main__':
    d = DashboardDB("data/dashboard.sqlite")
