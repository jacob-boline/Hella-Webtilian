from django.conf import settings
from django.db import migrations, models


def normalize_shop_text_fields(apps, schema_editor):
    Customer = apps.get_model('hr_shop', 'Customer')
    Order = apps.get_model('hr_shop', 'Order')
    CheckoutDraft = apps.get_model('hr_shop', 'CheckoutDraft')

    Customer.objects.filter(stripe_customer_id='').update(stripe_customer_id=None)
    Order.objects.filter(stripe_checkout_session_id='').update(stripe_checkout_session_id=None)
    Order.objects.filter(stripe_payment_intent_id='').update(stripe_payment_intent_id=None)

    Customer.objects.filter(middle_initial__isnull=True).update(middle_initial='')
    Customer.objects.filter(suffix__isnull=True).update(suffix='')
    Order.objects.filter(note__isnull=True).update(note='')
    CheckoutDraft.objects.filter(note__isnull=True).update(note='')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hr_shop', '0002_product_image_on_product'),
    ]

    operations = [
        migrations.RunPython(normalize_shop_text_fields, noop_reverse),
        migrations.AlterField(
            model_name='customer',
            name='middle_initial',
            field=models.CharField(blank=True, default='', max_length=5),
        ),
        migrations.AlterField(
            model_name='customer',
            name='suffix',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='orders', to='hr_shop.customer'),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='claimed_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='note',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
        migrations.AlterField(
            model_name='checkoutdraft',
            name='note',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
    ]
