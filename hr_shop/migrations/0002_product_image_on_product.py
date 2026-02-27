from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr_shop", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="products", to="hr_shop.productimage"),
        ),
    ]
