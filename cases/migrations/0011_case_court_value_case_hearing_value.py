# Generated by Django 5.1.7 on 2025-04-09 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0010_alter_case_clause_1_alter_case_clause_2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='court_value',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='hearing_value',
            field=models.TextField(blank=True, null=True),
        ),
    ]
