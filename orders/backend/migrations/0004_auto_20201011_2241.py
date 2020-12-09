# Generated by Django 3.1.2 on 2020-10-11 19:41

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_confirmemailtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'Пользователь с таким именем уже существует'}, help_text='Требуется имя пользователя. Буквы, цифры и @/./+/-/_.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='имя пользователя'),
        ),
    ]
