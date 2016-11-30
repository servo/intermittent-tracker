def on_label_added(db, label, issue_name, issue_number, state):
    if state != 'open':
        return
    if label == 'C-disabled':
        db.remove(issue_number)
        return
    elif label != 'I-intermittent':
        return
    db.add(issue_name, issue_number)

        
def on_label_removed(db, label, issue_name, issue_number, state):
    if state != 'open':
        return
    if label == 'C-disabled':
        db.add(issue_name, issue_number)
    if label != 'I-intermittent':
        return
    db.remove(issue_number)


def on_issue_closed(db, issue_number):
    db.remove(issue_number)


def on_issue_reopened(db, issue_name, issue_number, labels):
    if 'I-intermittent' not in labels or 'C-disabled' in labels:
        return
    db.add(issue_name, issue_number)


def on_issue_updated(db, issue_name, issue_number, labels, state):
    if state != 'open':
        return
    if 'I-intermittent' not in labels or 'C-disabled' in labels:
        return
    db.remove(issue_number)
    db.add(issue_name, issue_number)
