# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-16 09:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxa', '0003_auto_20160916_0946'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commonname',
            name='name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
