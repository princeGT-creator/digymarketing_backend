# Generated by Django 5.1.7 on 2025-05-27 04:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0014_case_payment_json_case_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='drive_folder_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
