import json
import os
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient

from app.config import settings


def serialize(doc):
    if isinstance(doc, list):
        return [serialize(x) for x in doc]
    if isinstance(doc, dict):
        return {k: serialize(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


def deserialize(doc):
    if isinstance(doc, list):
        return [deserialize(x) for x in doc]
    if isinstance(doc, dict):
        new_doc = {}
        for k, v in doc.items():
            if k == "_id" and isinstance(v, str) and len(v) == 24:
                try:
                    new_doc[k] = ObjectId(v)
                except Exception:
                    new_doc[k] = v
            elif isinstance(v, str) and (k == "created_at" or k.endswith("_at")):
                try:
                    new_doc[k] = datetime.fromisoformat(v)
                except Exception:
                    new_doc[k] = v
            else:
                new_doc[k] = deserialize(v)
        return new_doc
    return doc


class MockCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction=1):
        reverse = (direction == -1)
        def sort_key(doc):
            val = doc.get(key, "")
            if val is None:
                return ""
            return val
        self.docs.sort(key=sort_key, reverse=reverse)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def __iter__(self):
        return iter(self.docs)

    def __next__(self):
        return next(iter(self.docs))


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count


class DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class MockCollection:
    def __init__(self, db_file, collection_name):
        self.db_file = db_file
        self.name = collection_name

    def _load_data(self):
        if not os.path.exists(self.db_file):
            return []
        try:
            with open(self.db_file, "r") as f:
                data = json.load(f)
            collection_data = data.get(self.name, [])
            return deserialize(collection_data)
        except Exception:
            return []

    def _save_data(self, docs):
        data = {}
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        data[self.name] = serialize(docs)
        try:
            with open(self.db_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _match(self, doc, filter_dict):
        if not filter_dict:
            return True
        for k, v in filter_dict.items():
            if isinstance(v, dict):
                for op, val in v.items():
                    if op == "$exists":
                        exists = (k in doc)
                        if exists != val:
                            return False
                    elif op == "$ne":
                        if doc.get(k) == val:
                            return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    def find(self, filter_dict=None):
        docs = self._load_data()
        matched = [d for d in docs if self._match(d, filter_dict)]
        return MockCursor(matched)

    def find_one(self, filter_dict=None):
        docs = self._load_data()
        for d in docs:
            if self._match(d, filter_dict):
                return d
        return None

    def insert_one(self, document):
        docs = self._load_data()
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        docs.append(doc)
        self._save_data(docs)
        return InsertOneResult(doc["_id"])

    def update_one(self, filter_dict, update_dict, upsert=False):
        docs = self._load_data()
        matched_count = 0
        modified_count = 0
        set_data = update_dict.get("$set", {})
        
        for d in docs:
            if self._match(d, filter_dict):
                matched_count += 1
                d.update(set_data)
                modified_count += 1
                break
                
        if matched_count == 0 and upsert:
            doc = {}
            for k, v in filter_dict.items():
                if not isinstance(v, dict):
                    doc[k] = v
            doc.update(set_data)
            if "_id" not in doc:
                doc["_id"] = ObjectId()
            docs.append(doc)
            self._save_data(docs)
            return UpdateResult(0, 1)
            
        if modified_count > 0:
            self._save_data(docs)
            
        return UpdateResult(matched_count, modified_count)

    def delete_one(self, filter_dict):
        docs = self._load_data()
        deleted_count = 0
        for i, d in enumerate(docs):
            if self._match(d, filter_dict):
                docs.pop(i)
                deleted_count = 1
                break
        if deleted_count > 0:
            self._save_data(docs)
        return DeleteResult(deleted_count)

    def count_documents(self, filter_dict):
        docs = self._load_data()
        return sum(1 for d in docs if self._match(d, filter_dict))

    def aggregate(self, pipeline):
        docs = self._load_data()
        result = docs
        
        for stage in pipeline:
            if "$match" in stage:
                match_filter = stage["$match"]
                result = [d for d in result if self._match(d, match_filter)]
            elif "$group" in stage:
                group_config = stage["$group"]
                group_id_expr = group_config["_id"]
                field_name = group_id_expr.replace("$", "")
                groups = {}
                for d in result:
                    val = d.get(field_name)
                    if val is not None:
                        groups[val] = groups.get(val, 0) + 1
                result = [{"_id": k, "count": v} for k, v in groups.items()]
            elif "$sort" in stage:
                sort_config = stage["$sort"]
                for k, v in sort_config.items():
                    reverse = (v == -1)
                    result.sort(key=lambda x: x.get(k, 0), reverse=reverse)
            elif "$limit" in stage:
                limit_val = stage["$limit"]
                result = result[:limit_val]
                
        return result


try:
    client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
    # Ping to check if remote/local MongoDB is responsive
    client.admin.command('ping')
    db = client[settings.mongo_db_name]
    messages_collection = db["messages"]
    responses_collection = db["responses"]
    handover_collection = db["handover_requests"]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Warning: Could not connect to MongoDB ({e}). Falling back to local JSON database.")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_file = os.path.join(BASE_DIR, "mock_db.json")
    messages_collection = MockCollection(db_file, "messages")
    responses_collection = MockCollection(db_file, "responses")
    handover_collection = MockCollection(db_file, "handover_requests")

