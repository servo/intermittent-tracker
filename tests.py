from db import IntermittentsDB
import handlers
import json

with open('tests.json') as f:
    db = IntermittentsDB(json.loads(f.read()))

assert db.query('many-draw-calls.html') == 14391
assert db.query('2d.fillStyle.parse.css-color-4-rgba-4.html') == 14389
assert db.query('mozbrowserlocationchange_event.html') == None

db.add('foo.html', 12345)
assert db.query('foo.html') == 12345
db.remove(12345)
assert db.query('foo.html') == None

handlers.on_label_added(db, 'E-easy', 'foo.html', 12345, 'open')
assert db.query('foo.html') == None

handlers.on_label_added(db, 'I-intermittent', 'foo.html', 12345, 'open')
assert db.query('foo.html') == 12345

handlers.on_label_removed(db, 'E-easy', 'foo.html', 12345, 'open')
assert db.query('foo.html') == 12345

handlers.on_label_removed(db, 'I-intermittent', 'foo.html', 12345, 'open')
assert db.query('foo.html') == None

handlers.on_label_added(db, 'I-intermittent', 'foo.html', 12345, 'open')
handlers.on_label_added(db, 'C-disabled', 'foo.html', 12345, 'open')
assert db.query('foo.html') == None

handlers.on_label_removed(db, 'C-disabled', 'foo.html', 12345, 'open')
assert db.query('foo.html') == 12345

handlers.on_issue_updated(db, 'bar.html', 12345, ['I-intermittent'], 'open')
assert db.query('foo.html') == None
assert db.query('bar.html') == 12345

handlers.on_issue_closed(db, 12345)
assert db.query('bar.html') == None

handlers.on_issue_reopened(db, 'bar.html', 12345, ['I-intermittent'])
assert db.query('bar.html') == 12345

handlers.on_issue_closed(db, 12345)
assert db.query('bar.html') == None

handlers.on_issue_updated(db, 'baz.html', 12345, ['I-intermittent'], 'closed')
assert db.query('baz.html') == None

handlers.on_label_removed(db, 'I-intermittent', 'baz.html', 12345, 'closed')
handlers.on_label_added(db, 'I-intermittent', 'baz.html', 12345, 'closed')
handlers.on_label_added(db, 'C-disabled', 'baz.html', 12345, 'closed')

handlers.on_issue_reopened(db, 'baz.html', 12345, ['I-intermittent', 'C-disabled'])
assert db.query('bar.html') == None

print 'All tests passed.'
