import json
import sqlite3

class IssuesDB:
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
                CREATE TABLE "attempt" (
                "path" TEXT NOT NULL                        -- test name
                , "subtest" TEXT DEFAULT NULL
                , "expected" TEXT NOT NULL                  -- status e.g. PASS
                , "actual" TEXT NOT NULL                    -- status e.g. FAIL
                , "time" INTEGER DEFAULT (unixepoch())
                , "message" TEXT DEFAULT NULL               -- test output
                , "stack" TEXT DEFAULT NULL
                , "branch" TEXT DEFAULT NULL                -- e.g. auto, try
                , "build_url" TEXT DEFAULT NULL             -- e.g. https://github.com/servo/servo/actions/runs/4030556190/jobs/6929482570
                , "pull_url" TEXT DEFAULT NULL              -- e.g. https://github.com/servo/servo/pull/29306
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
            self.con.execute("COMMIT")


# python3 -im intermittent_tracker.db
if __name__ == '__main__':
    d = DashboardDB("data/dashboard.sqlite")
