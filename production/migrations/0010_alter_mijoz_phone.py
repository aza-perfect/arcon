# Generated by Django 5.0.14 on 2025-05-01 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0009_alter_sotuv_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mijoz',
            name='phone',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
