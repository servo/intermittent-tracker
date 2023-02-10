from .db import IssuesDB, DashboardDB, now
from . import fs, handlers
import time
import json

def debug(value):
    print(repr(value))
    return value

def query(db, name):
    result = db.query(name)
    if result:
        return result[0]['number']
    return None

db = IssuesDB.readonly(fs.TESTS_JSON_PATH)
assert query(db, 'many-draw-calls.html') == 14391
assert query(db, '2d.fillStyle.parse.css-color-4-rgba-4.html') == 14389
assert query(db, 'mozbrowserlocationchange_event.html') == None
assert len(db.query('Intermittent')) == 2

db.add('foo.html', 12345)
assert query(db, 'foo.html') == 12345
db.remove(12345)
assert query(db, 'foo.html') == None

handlers.on_label_added(db, 'E-easy', 'foo.html', 12345, 'open')
assert query(db, 'foo.html') == None

handlers.on_label_added(db, 'I-intermittent', 'foo.html', 12345, 'open')
assert query(db, 'foo.html') == 12345

handlers.on_label_removed(db, 'E-easy', 'foo.html', 12345, 'open')
assert query(db, 'foo.html') == 12345

handlers.on_label_removed(db, 'I-intermittent', 'foo.html', 12345, 'open')
assert query(db, 'foo.html') == None

handlers.on_label_added(db, 'I-intermittent', 'foo.html', 12345, 'open')
handlers.on_label_added(db, 'C-disabled', 'foo.html', 12345, 'open')
assert query(db, 'foo.html') == None

handlers.on_label_removed(db, 'C-disabled', 'foo.html', 12345, 'open')
assert query(db, 'foo.html') == 12345

handlers.on_issue_updated(db, 'bar.html', 12345, ['I-intermittent'], 'open')
assert query(db, 'foo.html') == None
assert query(db, 'bar.html') == 12345

handlers.on_issue_closed(db, 12345)
assert query(db, 'bar.html') == None

handlers.on_issue_reopened(db, 'bar.html', 12345, ['I-intermittent'])
assert query(db, 'bar.html') == 12345

handlers.on_issue_closed(db, 12345)
assert query(db, 'bar.html') == None

handlers.on_issue_updated(db, 'baz.html', 12345, ['I-intermittent'], 'closed')
assert query(db, 'baz.html') == None

handlers.on_label_removed(db, 'I-intermittent', 'baz.html', 12345, 'closed')
handlers.on_label_added(db, 'I-intermittent', 'baz.html', 12345, 'closed')
handlers.on_label_added(db, 'C-disabled', 'baz.html', 12345, 'closed')

handlers.on_issue_reopened(db, 'baz.html', 12345, ['I-intermittent', 'C-disabled'])
assert query(db, 'bar.html') == None


dashboard = DashboardDB(":memory:")

# insert output where hashes are unknown, due to being migrated from schema v1
dashboard.con.execute('INSERT INTO "output" VALUES (NULL,?,?,NULL,NULL)', ('m', 's'))

# insert eight attempts across two submissions with:
# • weird result timestamps, and two results that are completely identical
# • three results for the same test where the last result is expected
# • one expected result for a test with no other results
# • four results having both of (message,stack) = NULL
# • two unexpected results having one of (message,stack) = NULL
# • two unexpected results for the same test where subtest = NULL
#   (NULL is tricky, because it bypasses naïve UNIQUE constraints)
# • both submissions completely identical and having no NULL fields
#   (submissions should never be deduped or treated as UNIQUE)
dashboard.insert_attempts([
    {'path':'b','subtest':None,'expected':'FAIL','actual':'PASS','time':2},
    {'path':'a','subtest':'c','expected':'PASS','actual':'FAIL','time':1},
    {'path':'a','subtest':'c','expected':'PASS','actual':'FAIL','time':1},
    {'path':'a','subtest':'c','expected':'PASS','actual':'PASS','time':3},
    {'path':'a','subtest':'d','expected':'PASS','actual':'FAIL','time':2,'message':'m','stack':None},
    {'path':'b','subtest':None,'expected':'FAIL','actual':'PASS','time':1,'message':None,'stack':'s'},
    {'path':'a','subtest':'e','expected':'OK','actual':'ERROR','time':0,'message':'m','stack':'s'},
], branch='x', build_url='y', pull_url='z', time_for_testing=13)
dashboard.insert_attempts([
    {'path':'a','subtest':'f','expected':'PASS','actual':'PASS','time':3},
], branch='x', build_url='y', pull_url='z', time_for_testing=13)

# there should be five unique tests
tests = dashboard.con.execute('SELECT * FROM "test"')
assert debug(tuple(tests.fetchone())) == (1,'b','',None,2,2)  # last_unexpected = 2 !
assert debug(tuple(tests.fetchone())) == (2,'a','=c','c',2,1)  # (2,1) !
assert debug(tuple(tests.fetchone())) == (3,'a','=d','d',1,2)
assert debug(tuple(tests.fetchone())) == (4,'a','=e','e',1,0)
assert debug(tuple(tests.fetchone())) == (5,'a','=f','f',0,None)  # (0,None) !
assert tests.fetchone() is None

# there should be four unique outputs
outputs = dashboard.con.execute('SELECT * FROM "output"')
assert debug(tuple(outputs.fetchone())) == (1,'m','s',3775001192,453955339)  # reused and hashed!
assert debug(tuple(outputs.fetchone())) == (2,None,None,0,0)
assert debug(tuple(outputs.fetchone())) == (3,'m',None,3775001192,0)
assert debug(tuple(outputs.fetchone())) == (4,None,'s',0,453955339)
assert outputs.fetchone() is None

# there should be two(!) submissions
submissions = dashboard.con.execute('SELECT * FROM "submission"')
assert debug(tuple(submissions.fetchone())) == (1,13,'x','y','z')
assert debug(tuple(submissions.fetchone())) == (2,13,'x','y','z')
assert submissions.fetchone() is None

# there should be eight attempts
attempts = dashboard.con.execute('SELECT * FROM "attempt"')
assert debug(tuple(attempts.fetchone())) == (1,1,'FAIL','PASS',2,2,1)
assert debug(tuple(attempts.fetchone())) == (2,2,'PASS','FAIL',1,2,1)
assert debug(tuple(attempts.fetchone())) == (3,2,'PASS','FAIL',1,2,1)
assert debug(tuple(attempts.fetchone())) == (4,2,'PASS','PASS',3,2,1)
assert debug(tuple(attempts.fetchone())) == (5,3,'PASS','FAIL',2,3,1)
assert debug(tuple(attempts.fetchone())) == (6,1,'FAIL','PASS',1,4,1)
assert debug(tuple(attempts.fetchone())) == (7,4,'OK','ERROR',0,1,1)
assert debug(tuple(attempts.fetchone())) == (8,5,'PASS','PASS',3,2,2)
assert attempts.fetchone() is None

# there should be five unexpected attempts where attempt_id > 1,
# each with (path,subtest,message,stack,branch,build_url,pull_url) mixed in
attempts = dashboard.select_attempts(since=1)
assert debug(attempts.pop(0)) == {'path':'a','subtest':'c','attempt_id':2,'test':2,'expected':'PASS','actual':'FAIL','time':1,'output':2,'submission':1,'message':None,'stack':None,'branch':'x','build_url':'y','pull_url':'z'}
assert debug(attempts.pop(0)) == {'path':'a','subtest':'c','attempt_id':3,'test':2,'expected':'PASS','actual':'FAIL','time':1,'output':2,'submission':1,'message':None,'stack':None,'branch':'x','build_url':'y','pull_url':'z'}
assert debug(attempts.pop(0)) == {'path':'a','subtest':'d','attempt_id':5,'test':3,'expected':'PASS','actual':'FAIL','time':2,'output':3,'submission':1,'message':'m','stack':None,'branch':'x','build_url':'y','pull_url':'z'}
assert debug(attempts.pop(0)) == {'path':'b','subtest':None,'attempt_id':6,'test':1,'expected':'FAIL','actual':'PASS','time':1,'output':4,'submission':1,'message':None,'stack':'s','branch':'x','build_url':'y','pull_url':'z'}
assert debug(attempts.pop(0)) == {'path':'a','subtest':'e','attempt_id':7,'test':4,'expected':'OK','actual':'ERROR','time':0,'output':1,'submission':1,'message':'m','stack':'s','branch':'x','build_url':'y','pull_url':'z'}
assert attempts == []

print('All tests passed.')
