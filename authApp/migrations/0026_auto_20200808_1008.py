# Generated by Django 3.0.8 on 2020-08-08 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authApp', '0025_dependants_cccno'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dependants',
            name='approved',
            field=models.CharField(default='Pending', max_length=20),
        ),
    ]
