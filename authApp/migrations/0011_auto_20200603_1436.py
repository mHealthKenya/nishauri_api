# Generated by Django 3.0.6 on 2020-06-03 11:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authApp', '0010_auto_20200529_1710'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dependants',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='dependants',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='user',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='user',
            name='updated_at',
        ),
    ]
