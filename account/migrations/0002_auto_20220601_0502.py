# Generated by Django 3.0.5 on 2022-06-01 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='city',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Ciudad'),
        ),
    ]
