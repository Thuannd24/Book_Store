from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.IntegerField(db_index=True)),
                ('cart_id', models.IntegerField()),
                ('status', models.CharField(choices=[
                    ('PENDING', 'Pending'),
                    ('CREATED', 'Created'),
                    ('PAYMENT_CREATED', 'Payment Created'),
                    ('PAYMENT_RESERVED', 'Payment Reserved'),
                    ('SHIPMENT_CREATED', 'Shipment Created'),
                    ('SHIPMENT_RESERVED', 'Shipment Reserved'),
                    ('CONFIRMED', 'Confirmed'),
                    ('SHIPPING', 'Shipping'),
                    ('DELIVERED', 'Delivered'),
                    ('FAILED', 'Failed'),
                    ('COMPENSATING', 'Compensating'),
                    ('COMPENSATED', 'Compensated'),
                ], default='CREATED', max_length=32)),
                ('payment_method', models.CharField(max_length=32)),
                ('shipping_method', models.CharField(max_length=32)),
                ('shipping_address', models.TextField()),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('payment_status', models.CharField(blank=True, default='', max_length=32)),
                ('shipping_status', models.CharField(blank=True, default='', max_length=32)),
                ('promo_code', models.CharField(blank=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'orders',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=64, unique=True)),
                ('customer_id', models.IntegerField(db_index=True)),
                ('percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('max_discount_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[
                    ('UNUSED', 'Unused'),
                    ('RESERVED', 'Reserved'),
                    ('USED', 'Used'),
                    ('RETURNED', 'Returned'),
                    ('EXPIRED', 'Expired'),
                ], default='UNUSED', max_length=16)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_to', models.DateTimeField(blank=True, null=True)),
                ('applied_order_id', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'promo_codes',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['customer_id', 'status'], name='promo_customer_status_idx'),
                    models.Index(fields=['code', 'customer_id'], name='promo_code_customer_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='SagaLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.IntegerField(db_index=True)),
                ('step', models.CharField(max_length=64)),
                ('status', models.CharField(max_length=32)),
                ('payload', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'saga_logs',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_id', models.IntegerField()),
                ('book_title_snapshot', models.CharField(max_length=512)),
                ('price_snapshot', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField()),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
            ],
            options={
                'db_table': 'order_items',
            },
        ),
    ]

