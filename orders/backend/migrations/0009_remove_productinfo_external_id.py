# Generated by Django 3.1.2 on 2020-11-19 10:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_productinfo_external_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productinfo',
            name='external_id',
        ),
    ]
