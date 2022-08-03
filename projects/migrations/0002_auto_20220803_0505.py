# Generated by Django 3.0.5 on 2022-08-03 05:05

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='identificacion',
            new_name='comprador_id',
        ),
        migrations.RenameField(
            model_name='bill',
            old_name='beneficiario',
            new_name='comprador_nombre',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='id_beneficiario',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='nombre',
        ),
        migrations.AddField(
            model_name='bill',
            name='beneficiario_id',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='beneficiario_nombre',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='comprador_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='comprador_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None),
        ),
        migrations.AlterField(
            model_name='bill',
            name='address_line_2',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='address_type',
            field=models.CharField(blank=True, choices=[('B', 'Billing'), ('S', 'Shipping')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='beneficiario_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
