# Generated by Django 3.0.5 on 2022-02-25 18:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_auto_20220215_0806'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='activation_key',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='key_expires',
        ),
    ]
