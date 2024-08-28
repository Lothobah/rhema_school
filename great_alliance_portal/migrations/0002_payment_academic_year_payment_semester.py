# Generated by Django 5.0.7 on 2024-08-13 19:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('great_alliance_portal', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='academic_year',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='great_alliance_portal.academic_year'),
        ),
        migrations.AddField(
            model_name='payment',
            name='semester',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='great_alliance_portal.semester'),
        ),
    ]
