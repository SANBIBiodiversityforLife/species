# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-01-24 14:00
from __future__ import unicode_literals

import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('people', '0001_initial'),
        ('taxa', '0007_auto_20170124_1557'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, unique=True)),
                ('action_type', models.CharField(choices=[('R', 'Research'), ('C', 'Conservation')], max_length=1)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ActionNature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verbose', models.TextField()),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redlist.Action')),
            ],
        ),
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scope', models.CharField(choices=[('N', 'Regional (South Africa)'), ('R', 'Regional (Other)'), ('G', 'Global')], default='N', max_length=1)),
                ('rationale', models.TextField()),
                ('change_rationale', models.TextField()),
                ('date', models.DateField()),
                ('notes', models.TextField()),
                ('redlist_category', models.CharField(choices=[('EX', 'EX'), ('EW', 'EW'), ('CR', 'CR'), ('EN', 'EN'), ('VU', 'VU'), ('NT', 'NT'), ('LC', 'LC'), ('DD', 'DD'), ('NE', 'NE')], max_length=2)),
                ('redlist_criteria', models.CharField(max_length=100)),
                ('population_size', django.contrib.postgres.fields.ranges.IntegerRangeField(blank=True, null=True)),
                ('subpopulation_number', django.contrib.postgres.fields.ranges.IntegerRangeField(blank=True, null=True)),
                ('population_trend_past', django.contrib.postgres.fields.ranges.IntegerRangeField(blank=True, null=True)),
                ('population_trend_future', django.contrib.postgres.fields.ranges.IntegerRangeField(blank=True, null=True)),
                ('population_trend_nature', models.CharField(blank=True, choices=[('U', 'Understood'), ('R', 'Reversible'), ('C', 'Ceased')], max_length=1, null=True)),
                ('population_trend_narrative', models.TextField(blank=True)),
                ('conservation_actions', models.ManyToManyField(to='redlist.Action')),
            ],
        ),
        migrations.CreateModel(
            name='Contribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.PositiveSmallIntegerField()),
                ('type', models.CharField(choices=[('A', 'Assessor'), ('R', 'Reviewer')], max_length=1)),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redlist.Assessment')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Person')),
            ],
        ),
        migrations.CreateModel(
            name='Threat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ThreatNature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('impact', models.CharField(choices=[('EX', 'Extreme'), ('SE', 'Severe'), ('MO', 'Moderate'), ('SL', 'Slight'), ('NO', 'None'), ('UN', 'Unknown')], default='UN', max_length=2)),
                ('timing', models.CharField(choices=[('PA', 'Past'), ('UR', 'Unlikely to return'), ('LR', 'Likely to return'), ('ON', 'Ongoing'), ('FU', 'Future'), ('PO', 'Potential'), ('UN', 'Unknown')], default='UN', max_length=2)),
                ('rationale', models.TextField(blank=True)),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redlist.Assessment')),
                ('threat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redlist.Threat')),
            ],
        ),
        migrations.AddField(
            model_name='assessment',
            name='contributors',
            field=models.ManyToManyField(through='redlist.Contribution', to='people.Person'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='taxa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taxa.Taxon'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='threats',
            field=models.ManyToManyField(through='redlist.ThreatNature', to='redlist.Threat'),
        ),
        migrations.AddField(
            model_name='actionnature',
            name='assessment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redlist.Assessment'),
        ),
    ]