CREATE TABLE "meta" (
    "version" INTEGER NOT NULL
);

-- dashboard.2.sql should UPDATE "meta" SET "version" = 2; and so on
INSERT INTO "meta" VALUES (1);

CREATE TABLE "test" (
    "test_id" INTEGER PRIMARY KEY
    , "path" TEXT NOT NULL                      -- test name
    , "subtest" TEXT DEFAULT NULL               -- subtest name
    , "unexpected_count" INTEGER NOT NULL
    , "last_unexpected" INTEGER                 -- unix time in seconds
);

CREATE INDEX "test.path" ON "test" ("path");
CREATE INDEX "test.subtest" ON "test" ("subtest");

CREATE TABLE "output" (
    "output_id" INTEGER PRIMARY KEY
    , "message" TEXT DEFAULT NULL               -- test output
    , "stack" TEXT DEFAULT NULL
    , "message_hash" INTEGER NOT NULL           -- crc32(message) or 0 if message is NULL
    , "stack_hash" INTEGER NOT NULL             -- crc32(stack) or 0 if stack is NULL
);

CREATE INDEX "output.hash" ON "output" ("message_hash", "stack_hash");

CREATE TABLE "submission" (
    "submission_id" INTEGER PRIMARY KEY
    , "time" INTEGER NOT NULL                   -- when results were submitted (unix time in seconds)
    , "branch" TEXT DEFAULT NULL                -- e.g. auto, try
    , "build_url" TEXT DEFAULT NULL             -- e.g. https://github.com/servo/servo/actions/runs/4030556190/jobs/6929482570
    , "pull_url" TEXT DEFAULT NULL              -- e.g. https://github.com/servo/servo/pull/29306
);

CREATE INDEX "submission.time" ON "submission" ("time" DESC);
CREATE INDEX "submission.branch" ON "submission" ("branch");
CREATE INDEX "submission.build_url" ON "submission" ("build_url");
CREATE INDEX "submission.pull_url" ON "submission" ("pull_url");

CREATE TABLE "attempt" (
    "attempt_id" INTEGER PRIMARY KEY
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

CREATE INDEX "attempt.expected" ON "attempt" ("expected");
CREATE INDEX "attempt.actual" ON "attempt" ("actual");
CREATE INDEX "attempt.time" ON "attempt" ("time" DESC);
