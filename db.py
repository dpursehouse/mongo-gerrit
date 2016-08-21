from pymongo import MongoClient, ASCENDING


class GerritMongoDatabase:
    def __init__(self, name, host, port):
        client = MongoClient(host=host, port=port)
        self.name = name
        db = client[self.name]
        self.changes = db.changes
        self.meta = db.meta
        self.changes.create_index([('id', ASCENDING)], unique=True)
        self.meta.create_index([('name', ASCENDING)], unique=True)

    def get_last_update(self):
        metadata = self.meta.find_one({'name': self.name})
        if metadata:
            return metadata['last-update']
        return None

    def set_last_update(self, timestamp):
        update_filter = {'name': self.name}
        update = {'name': self.name, 'last-update': timestamp}
        self.meta.replace_one(update_filter, update, upsert=True)

    def update_change(self, change):
        self.changes.replace_one(
            {'id': change['id']},
            change,
            bypass_document_validation=True,
            upsert=True)

    def change_count(self):
        return self.changes.count()
