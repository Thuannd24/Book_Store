import os

import psycopg2
import django
from pymongo.errors import PyMongoError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from comment_rate.infrastructure.mongo import (
    ensure_indexes,
    get_reviews_collection,
    set_review_sequence_if_higher,
)


def _migrate() -> int:
    postgres_url = os.getenv('POSTGRES_MIGRATION_URL', '').strip()
    if not postgres_url:
        print('POSTGRES_MIGRATION_URL not set. Skip PostgreSQL -> MongoDB migration.')
        return 0

    collection = get_reviews_collection()
    existing = collection.count_documents({})
    if existing > 0:
        print(f'MongoDB already has {existing} reviews. Skip migration.')
        return 0

    conn = psycopg2.connect(postgres_url)
    migrated_count = 0
    max_id = 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, book_id, customer_id, rating, comment, status, created_at
                FROM reviews
                ORDER BY id
                """
            )
            rows = cur.fetchall()

        documents = []
        for row in rows:
            row_id, book_id, customer_id, rating, comment, status, created_at = row
            max_id = max(max_id, int(row_id))
            documents.append(
                {
                    'id': int(row_id),
                    'book_id': int(book_id),
                    'customer_id': int(customer_id),
                    'rating': int(rating),
                    'comment': comment or '',
                    'status': status or 'ACTIVE',
                    'created_at': created_at,
                }
            )

        if documents:
            collection.insert_many(documents, ordered=True)
            migrated_count = len(documents)

        set_review_sequence_if_higher(max_id)
        print(f'Migrated {migrated_count} reviews from PostgreSQL to MongoDB.')
        return migrated_count
    finally:
        conn.close()


def main() -> int:
    try:
        ensure_indexes()
        _migrate()
        return 0
    except PyMongoError as exc:
        print(f'MongoDB migration error: {exc}')
        return 1
    except Exception as exc:
        print(f'Unexpected migration error: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
