CREATE TABLE "meta" (
    "version" INTEGER NOT NULL
);

-- dashboard.2.sql should UPDATE "meta" SET "version" = 2; and so on
INSERT INTO "meta" VALUES (1);

-- tests are identified by (path,subtest), but some tests are not subtests.
-- the obvious representation for such tests would be (path,NULL), but sqlite
-- makes the (legal) decision to allow (path,NULL) to effectively bypass
--
-- 1.  PRIMARY KEY constraints (“Each row in a table with a primary key must have a unique
--     combination of values in its primary key columns. For the purposes of determining the
--     uniqueness of primary key values, NULL values are considered distinct from all other
--     values, including other NULLs.”)
--
-- 2.  UNIQUE constraints (“For each UNIQUE constraint on the table, each row must contain a unique
--     combination of values in the columns identified by the UNIQUE constraint. For the purposes of
--     UNIQUE constraints, NULL values are considered distinct from all other values, including
--     other NULLs.”)
--
-- 3.  FOREIGN KEY constraints (“The foreign key constraint is satisfied if for each row in the
--     child table either one or more of the child key columns are NULL, or there exists a row in
--     the parent table for which each parent key column contains a value equal to the value in its
--     associated child key column.”)
--
-- we want (path,NULL) to be treated like an ordinary value, but we can’t have
-- that, so let’s represent tests here as (path,'') and (path,'='+subtest).

CREATE TABLE "test" (
    "path" TEXT NOT NULL                        -- test name
    , "subtest" TEXT NOT NULL                   -- if subtest, '='+subtest, else ''
    , "unexpected_count" INTEGER NOT NULL
    , "last_unexpected" INTEGER                 -- unix time
    , PRIMARY KEY ("path", "subtest")
);

CREATE TABLE "attempt" (
    "path" TEXT NOT NULL                        -- test name
    , "subtest" TEXT NOT NULL                   -- if subtest, '='+subtest, else ''
    , "expected" TEXT NOT NULL                  -- status e.g. PASS
    , "actual" TEXT NOT NULL                    -- status e.g. FAIL
    , "time" INTEGER NOT NULL                   -- unix time
    , "message" TEXT DEFAULT NULL               -- test output
    , "stack" TEXT DEFAULT NULL
    , "branch" TEXT DEFAULT NULL                -- e.g. auto, try
    , "build_url" TEXT DEFAULT NULL             -- e.g. https://github.com/servo/servo/actions/runs/4030556190/jobs/6929482570
    , "pull_url" TEXT DEFAULT NULL              -- e.g. https://github.com/servo/servo/pull/29306
    , FOREIGN KEY ("path", "subtest") REFERENCES "test"
);

CREATE INDEX "attempt.test" ON "attempt" ("path", "subtest");
CREATE INDEX "attempt.build" ON "attempt" ("build_url");
CREATE INDEX "attempt.pull" ON "attempt" ("pull_url");
