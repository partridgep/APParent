# Generated by Django 3.1 on 2020-09-19 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0004_auto_20200919_1227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='child',
            field=models.ManyToManyField(to='main_app.Child'),
        ),
    ]
