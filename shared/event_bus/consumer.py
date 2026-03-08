import json
import logging
import os

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')


def consume_events(exchange: str, queue_name: str, routing_keys: list, callback):
    """Start consuming events from RabbitMQ."""
    import pika
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
    channel.queue_declare(queue=queue_name, durable=True)
    for key in routing_keys:
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=key)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    logger.info('Consuming from queue %s', queue_name)
    channel.start_consuming()
