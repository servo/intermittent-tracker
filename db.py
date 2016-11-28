import json

class IntermittentsDB:
    def __init__(self, db):
        self.intermittents = db


    def query(self, name):
        for i in self.intermittents:
            if name in i['title']:
                return i
        return None


    def add(self, name, number):
        for i in self.intermittents:
            if i['number'] == number:
                return
        self.intermittents.extend([{'title': name, 'number': number}])

    
    def remove(self, number):
        for idx, i in enumerate(self.intermittents):
            if i['number'] == number:
                self.intermittents.pop(idx)
                return


class AutoWriteDB(IntermittentsDB):
    def __init__(self, filename):
        self.filename = filename
        with open(filename) as f:
            IntermittentsDB.__init__(json.loads(f.read()))

    def __enter__(self):
        return self

    def __exit__(self):
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.intermittents))
