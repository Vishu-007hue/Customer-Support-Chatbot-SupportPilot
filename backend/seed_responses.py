from app.db.mongo import responses_collection


def main() -> None:
    seed = [
        {"intent": "Greeting", "variants": ["Hello! How can I help you today?"]},
        {
            "intent": "Order_Status",
            "variants": ["Please share your order ID and I will check the status."],
        },
        {
            "intent": "Refund_Request",
            "variants": ["I can help with refunds. Please provide your order ID and reason."],
        },
        {
            "intent": "Complaint_Product",
            "variants": ["I am sorry you faced this issue. Please describe the problem briefly."],
        },
        {"intent": "Goodbye", "variants": ["Thanks for contacting support. Have a great day!"]},
    ]

    for item in seed:
        responses_collection.update_one(
            {"intent": item["intent"]}, {"$set": item}, upsert=True
        )

    print("Seeded responses collection.")


if __name__ == "__main__":
    main()
