# Generated by Django 3.1.2 on 2020-11-18 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_shop_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='name',
            field=models.CharField(default=None, max_length=50, verbose_name='Название'),
        ),
    ]
