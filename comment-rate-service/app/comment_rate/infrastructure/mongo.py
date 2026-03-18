from datetime import datetime, timezone

from django.conf import settings
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_mongo_db() -> Database:
    client = get_mongo_client()
    return client[settings.MONGO_DB_NAME]


def ensure_indexes() -> None:
    collection = get_reviews_collection()
    collection.create_index([('id', ASCENDING)], unique=True, name='reviews_id_unique')
    collection.create_index([('book_id', ASCENDING), ('status', ASCENDING)], name='reviews_book_status_idx')
    collection.create_index([('customer_id', ASCENDING), ('status', ASCENDING)], name='reviews_customer_status_idx')
    collection.create_index([('created_at', DESCENDING)], name='reviews_created_at_idx')


def get_reviews_collection() -> Collection:
    db = get_mongo_db()
    return db['reviews']


def get_next_review_id() -> int:
    db = get_mongo_db()
    counter = db['counters'].find_one_and_update(
        {'_id': 'reviews'},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(counter['seq'])


def set_review_sequence_if_higher(current_max_id: int) -> None:
    db = get_mongo_db()
    db['counters'].update_one(
        {'_id': 'reviews'},
        {'$max': {'seq': int(current_max_id)}},
        upsert=True,
    )


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def check_mongo_health() -> bool:
    try:
        get_mongo_client().admin.command('ping')
        return True
    except PyMongoError:
        return False
