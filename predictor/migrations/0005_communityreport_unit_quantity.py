# Generated migration for adding unit_quantity field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictor', '0004_communityreport_commodity_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='communityreport',
            name='unit_quantity',
            field=models.CharField(default='1 kg', help_text='e.g., 1 kg, 2 lbs, 1 piece', max_length=20),
        ),
    ]