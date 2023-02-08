-- this migration adds a column representing the submission time, synthesised
-- for existing data as max(attempt.time).

-- to save space in the attempt table (7.4 MB to 1.2 MB for 6 full wpt runs),
-- replace (path,subtest) with an integer foreign key into the test table,
-- move (branch,build_url,pull_url), which are likely to be the same within a
-- POST /dashboard/attempts request, to a new submission table, and move
-- (message,stack), which are large but repetitive, to a new output table.

-- we also remove unnecessary indices over (path,subtest), make indices over
-- (time) columns descending, and use partial indices for columns that might be
-- null, since the dashboard api doesn’t yet allow searching for null anyway.

-- the new rowid alias columns are foo.foo_id, which is a bit redundant, but
-- avoids accidentally shadowing "id" in row dicts for queries with joins
-- (sqlite only warns about ambiguity when using "id" in an expression).
UPDATE "meta" SET "version" = 2;


CREATE TABLE "submission" (
    "submission_id" INTEGER PRIMARY KEY         -- rowid alias (for foreign key)
    , "time" INTEGER NOT NULL                   -- when results were submitted (unix time in seconds)
    , "branch" TEXT DEFAULT NULL                -- e.g. auto, try
    , "build_url" TEXT DEFAULT NULL             -- e.g. https://github.com/servo/servo/actions/runs/4030556190/jobs/6929482570
    , "pull_url" TEXT DEFAULT NULL              -- e.g. https://github.com/servo/servo/pull/29306
);

CREATE INDEX "submission.time" ON "submission" ("time" DESC);
CREATE INDEX "submission.branch" ON "submission" ("branch") WHERE "branch" IS NOT NULL;
CREATE INDEX "submission.build_url" ON "submission" ("build_url") WHERE "build_url" IS NOT NULL;
CREATE INDEX "submission.pull_url" ON "submission" ("pull_url") WHERE "pull_url" IS NOT NULL;

INSERT INTO "submission" ("time", "branch", "build_url", "pull_url")
SELECT DISTINCT max("time") AS "time", "branch", "build_url", "pull_url"
FROM "attempt" GROUP BY "branch", "build_url", "pull_url";


CREATE TABLE "output" (
    "output_id" INTEGER PRIMARY KEY             -- rowid alias (for foreign key)
    , "message" TEXT DEFAULT NULL               -- test output
    , "stack" TEXT DEFAULT NULL
    , "message_hash" INTEGER DEFAULT NULL       -- crc32(message) or 0 if message is NULL, or NULL if unknown
    , "stack_hash" INTEGER DEFAULT NULL         -- crc32(stack) or 0 if stack is NULL, or NULL if unknown
    -- , UNIQUE ("message", "stack")            -- constraint index wastes disk space
);

CREATE INDEX "output.hash" ON "output" ("message_hash", "stack_hash");

INSERT INTO "output" ("message", "stack")
SELECT DISTINCT "message", "stack"
FROM "attempt" GROUP BY "message", "stack";


-- https://sqlite.org/lang_altertable.html#making_other_kinds_of_table_schema_changes
CREATE TABLE "_new_test" (
    "test_id" INTEGER PRIMARY KEY               -- rowid alias (for foreign key)
    , "path" TEXT NOT NULL                      -- test name
    , "_subtest" TEXT NOT NULL AS (IIF(         -- for constraints [1]
        "subtest" IS NULL, '', '=' || "subtest"))
    , "subtest" TEXT                            -- actual subtest name
    , "unexpected_count" INTEGER NOT NULL
    , "last_unexpected" INTEGER                 -- unix time
    , UNIQUE ("path", "_subtest")
);

INSERT INTO "_new_test" ("path", "subtest", "unexpected_count", "last_unexpected")
SELECT "path", "subtest", "unexpected_count", "last_unexpected"
FROM "test";

DROP TABLE "test";
ALTER TABLE "_new_test" RENAME TO "test";

CREATE INDEX "test.path" ON "test" ("path");
CREATE INDEX "test.subtest" ON "test" ("subtest") WHERE "subtest" IS NOT NULL;


-- https://sqlite.org/lang_altertable.html#making_other_kinds_of_table_schema_changes
CREATE TABLE "_new_attempt" (
    "attempt_id" INTEGER PRIMARY KEY            -- rowid alias (but stable under VACUUM)
    , "test" INTEGER NOT NULL                   -- test id
    , "expected" TEXT NOT NULL                  -- status e.g. PASS
    , "actual" TEXT NOT NULL                    -- status e.g. FAIL
    , "time" INTEGER NOT NULL                   -- when test was run (unix time in seconds)
    , "output" INTEGER NOT NULL                 -- output id
    , "submission" INTEGER NOT NULL             -- submission id
    , FOREIGN KEY ("test") REFERENCES "test"
    , FOREIGN KEY ("output") REFERENCES "output"
    , FOREIGN KEY ("submission") REFERENCES "submission"
);

INSERT INTO "_new_attempt" ("test", "expected", "actual", "time", "output", "submission")
SELECT "test_id" AS "test", "expected", "actual", "attempt"."time", "output_id" AS "output", "submission_id" AS "submission"
FROM "attempt", "test", "output", "submission"
WHERE "attempt"."path" IS "test"."path"
AND "attempt"."subtest" IS "test"."subtest"
AND "attempt"."message" IS "output"."message"
AND "attempt"."stack" IS "output"."stack"
AND "attempt"."branch" IS "submission"."branch"
AND "attempt"."build_url" IS "submission"."build_url"
AND "attempt"."pull_url" IS "submission"."pull_url";

DROP TABLE "attempt";
ALTER TABLE "_new_attempt" RENAME TO "attempt";

CREATE INDEX "attempt.expected" ON "attempt" ("expected");
CREATE INDEX "attempt.actual" ON "attempt" ("actual");
CREATE INDEX "attempt.time" ON "attempt" ("time" DESC);
