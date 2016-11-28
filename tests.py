from db import IntermittentsDB
import handlers
import json

def query(db, name):
    result = db.query(name)
    if result:
        return result['number']
    return None

with open('tests.json') as f:
    db = IntermittentsDB(json.loads(f.read()))

assert query(db, 'many-draw-calls.html') == 14391
assert query(db, '2d.fillStyle.parse.css-color-4-rgba-4.html') == 14389
assert query(db, 'mozbrowserlocationchange_event.html') == None

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

print 'All tests passed.'
