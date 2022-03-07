# Generated by Django 3.0.5 on 2022-03-03 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_commissionagent_projectbyinvestor_subscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Visitor'), (2, 'One Time Investment'), (3, 'Subscription Investment'), (4, 'Admin')], null=True),
        ),
    ]
