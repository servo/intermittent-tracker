from .db import IssuesDB, DashboardDB
from . import fs, handlers
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
dashboard.insert_attempts([
    {'path':'a','subtest':'b','expected':'FAIL','actual':'PASS','time':1},
    {'path':'a','subtest':'c','expected':'PASS','actual':'PASS','time':2},
])
tests = dashboard.con.execute('SELECT * FROM "test"').fetchall()
assert debug([tuple(x) for x in tests]) == [(1,'a','=b','b',1,1), (2,'a','=c','c',0,None)]
outputs = dashboard.con.execute('SELECT * FROM "output"').fetchall()
assert debug([tuple(x) for x in outputs]) == [(1,None,None,0,0)]
attempts = dashboard.con.execute('SELECT * FROM "attempt"')
assert debug(tuple(attempts.fetchone())) == (1,1,'FAIL','PASS',1,1,1)
assert debug(tuple(attempts.fetchone())) == (2,2,'PASS','PASS',2,1,1)

dashboard.insert_attempts([{'path':'a','subtest':'c','expected':'PASS','actual':'FAIL','time':3}])
tests = dashboard.con.execute('SELECT * FROM "test"').fetchall()
assert debug([tuple(x) for x in tests]) == [(1,'a','=b','b',1,1), (2,'a','=c','c',1,3)]


print('All tests passed.')
