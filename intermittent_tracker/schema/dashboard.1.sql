CREATE TABLE "meta" (
    "version" INTEGER NOT NULL
);

-- dashboard.2.sql should UPDATE "meta" SET "version" = 2; and so on
INSERT INTO "meta" VALUES (1);

CREATE TABLE "test" (
    "path" TEXT NOT NULL                        -- test name
    , "_subtest" TEXT NOT NULL AS (IIF(         -- for constraints [1]
        "subtest" IS NULL, '', '=' || "subtest"))
    , "subtest" TEXT                            -- actual subtest name
    , "unexpected_count" INTEGER NOT NULL
    , "last_unexpected" INTEGER                 -- unix time
    , UNIQUE ("path", "_subtest")
);

CREATE TABLE "attempt" (
    "path" TEXT NOT NULL                        -- test name
    , "_subtest" TEXT NOT NULL AS (IIF(         -- for constraints [1]
        "subtest" IS NULL, '', '=' || "subtest"))
    , "subtest" TEXT                            -- actual subtest name
    , "expected" TEXT NOT NULL                  -- status e.g. PASS
    , "actual" TEXT NOT NULL                    -- status e.g. FAIL
    , "time" INTEGER NOT NULL                   -- unix time
    , "message" TEXT DEFAULT NULL               -- test output
    , "stack" TEXT DEFAULT NULL
    , "branch" TEXT DEFAULT NULL                -- e.g. auto, try
    , "build_url" TEXT DEFAULT NULL             -- e.g. https://github.com/servo/servo/actions/runs/4030556190/jobs/6929482570
    , "pull_url" TEXT DEFAULT NULL              -- e.g. https://github.com/servo/servo/pull/29306
    , FOREIGN KEY ("path", "_subtest") REFERENCES "test"
);

CREATE INDEX "attempt.test" ON "attempt" ("path", "subtest");
CREATE INDEX "attempt.branch" ON "attempt" ("branch");
CREATE INDEX "attempt.build" ON "attempt" ("build_url");
CREATE INDEX "attempt.pull" ON "attempt" ("pull_url");

-- [1] tests are identified by (path,subtest), or (path,NULL) if the test is not
-- a subtest, but sqlite makes the (legal) decision to let (path,NULL) bypass
-- PRIMARY KEY constraints, UNIQUE constraints, and FOREIGN KEY constraints.
-- we can work around this by mapping NULL to '' and 'foo' to '='||'foo' in a
-- generated column, giving us the behaviour we want when used in constraints.
-- https://sqlite.org/lang_createtable.html#the_primary_key
-- https://sqlite.org/lang_createtable.html#unique_constraints
-- https://sqlite.org/foreignkeys.html#fk_basics
