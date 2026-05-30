from app.db.mongo import handover_collection, messages_collection
from app.models.schemas import AnalyticsSummary


class AnalyticsService:
    def summary(self) -> AnalyticsSummary:
        total_queries = messages_collection.count_documents({"sender": "user"})
        bot_messages = messages_collection.count_documents({"sender": "bot"})
        handover_count = handover_collection.count_documents({})

        pipeline = [
            {"$match": {"intent": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
        ]
        top_intents = [
            {"intent": row["_id"], "count": row["count"]}
            for row in messages_collection.aggregate(pipeline)
        ]

        return AnalyticsSummary(
            total_queries=total_queries,
            bot_messages=bot_messages,
            handover_count=handover_count,
            top_intents=top_intents,
        )
