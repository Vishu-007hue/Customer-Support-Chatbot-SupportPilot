# pyrefly: ignore [missing-import]
from bson import ObjectId
# pyrefly: ignore [missing-import]
from bson.errors import InvalidId

from app.db.mongo import responses_collection
from app.models.schemas import ResponseRecordIn, ResponseRecordOut


class AdminService:
    def list_responses(self) -> list[ResponseRecordOut]:
        records: list[ResponseRecordOut] = []
        for item in responses_collection.find().sort("intent", 1):
            records.append(
                ResponseRecordOut(
                    id=str(item["_id"]),
                    intent=item.get("intent", ""),
                    variants=item.get("variants", []),
                    tags=item.get("tags", []),
                )
            )
        return records

    def create_response(self, payload: ResponseRecordIn) -> ResponseRecordOut:
        doc = payload.model_dump()
        result = responses_collection.insert_one(doc)
        return ResponseRecordOut(id=str(result.inserted_id), **doc)

    def update_response(self, record_id: str, payload: ResponseRecordIn) -> ResponseRecordOut | None:
        updates = payload.model_dump()
        try:
            object_id = ObjectId(record_id)
        except InvalidId:
            return None
        result = responses_collection.update_one(
            {"_id": object_id},
            {"$set": updates},
        )
        if result.matched_count == 0:
            return None
        updated = responses_collection.find_one({"_id": object_id})
        return ResponseRecordOut(
            id=str(updated["_id"]),
            intent=updated.get("intent", ""),
            variants=updated.get("variants", []),
            tags=updated.get("tags", []),
        )

    def delete_response(self, record_id: str) -> bool:
        try:
            object_id = ObjectId(record_id)
        except InvalidId:
            return False
        result = responses_collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
