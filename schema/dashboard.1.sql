CREATE TABLE "meta" (
    "version" INTEGER NOT NULL
);

-- dashboard.2.sql should UPDATE "meta" SET "version" = 2; and so on
INSERT INTO "meta" VALUES (1);

CREATE TABLE "test" (
    "path" TEXT NOT NULL                        -- test name
    , "subtest" TEXT
    , "unexpected_count" INTEGER NOT NULL
    , "last_unexpected" INTEGER                 -- unix time
    , PRIMARY KEY ("path", "subtest")
);

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
);

CREATE INDEX "attempt.test" ON "attempt" ("path", "subtest");
CREATE INDEX "attempt.build" ON "attempt" ("build_url");
CREATE INDEX "attempt.pull" ON "attempt" ("pull_url");

CREATE TRIGGER "test.count_unexpected" INSERT ON "attempt" BEGIN
    INSERT INTO "test" VALUES (
        new."path", new."subtest"
        , CASE WHEN new."actual" != new."expected" THEN 1 ELSE 0 END
        , CASE WHEN new."actual" != new."expected" THEN new."time" ELSE NULL END
    ) ON CONFLICT DO UPDATE SET
        "unexpected_count" = "unexpected_count" + 1
        , "last_unexpected" = new."time"
        WHERE new."actual" != new."expected";
END;
