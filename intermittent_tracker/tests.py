from db import IssuesDB, DashboardDB
import handlers
import json

def query(db, name):
    result = db.query(name)
    if result:
        return result[0]['number']
    return None

db = IssuesDB.readonly('tests.json')
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
dashboard.insert_attempts(
    {'path':'a','subtest':'b','expected':'FAIL','actual':'PASS','time':1},
    {'path':'a','subtest':'c','expected':'PASS','actual':'PASS','time':2})
tests = dashboard.con.execute('SELECT * FROM "test"').fetchall()
assert [tuple(x) for x in tests] == [('a','b',1,1), ('a','c',0,None)]
attempts = dashboard.con.execute('SELECT * FROM "attempt"')
assert tuple(attempts.fetchone()) == ('a','b','FAIL','PASS',1,None,None,None,None,None)
assert tuple(attempts.fetchone()) == ('a','c','PASS','PASS',2,None,None,None,None,None)

dashboard.insert_attempt(path='a', subtest='c', expected='PASS', actual='FAIL', time=3)
tests = dashboard.con.execute('SELECT * FROM "test"').fetchall()
assert [tuple(x) for x in tests] == [('a','b',1,1), ('a','c',1,3)]


print('All tests passed.')
