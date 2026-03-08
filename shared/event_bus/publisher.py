import json
import logging
import os

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')


def publish_event(exchange: str, routing_key: str, payload: dict):
    """Publish an event to RabbitMQ. Fire-and-forget, logs on failure."""
    try:
        import pika
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type='application/json',
            ),
        )
        connection.close()
        logger.info('Published event %s to %s', routing_key, exchange)
    except Exception as exc:
        logger.error('Failed to publish event %s: %s', routing_key, exc)
