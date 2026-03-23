import json
import logging
import os
import pika

from django.core.management.base import BaseCommand
from books.application.services import BookService

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://bookstore:bookstore123@rabbitmq:5672/')

EXCHANGE_ORDERS = 'orders'
ROUTING_KEY_CONFIRMED = 'order.confirmed'
QUEUE_NAME = 'book_service_orders'


class Command(BaseCommand):
    help = 'Consume order.confirmed events from RabbitMQ to decrement stock'

    def handle(self, *args, **options):
        logger.info('Starting Order Confirmed Consumer...')
        
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(exchange=EXCHANGE_ORDERS, exchange_type='topic', durable=True)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_bind(exchange=EXCHANGE_ORDERS, queue=QUEUE_NAME, routing_key=ROUTING_KEY_CONFIRMED)

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body)
                    order_id = payload.get('order_id')
                    items = payload.get('items', [])
                    
                    logger.info('Processing order.confirmed for order %s', order_id)
                    
                    if items:
                        BookService.decrement_stock(items)
                        logger.info('Successfully decremented stock for order %s', order_id)
                    else:
                        logger.warning('Order %s has no items to decrement stock.', order_id)
                    
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as exc:
                    logger.error('Error processing message: %s', exc)
                    # For demo simplicity, we ack to avoid infinite retry, but in prod we might DLQ
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
            
            logger.info('Order Consumer is waiting for messages. To exit press CTRL+C')
            channel.start_consuming()

        except Exception as e:
            logger.error('RabbitMQ Consumer error: %s', e)
