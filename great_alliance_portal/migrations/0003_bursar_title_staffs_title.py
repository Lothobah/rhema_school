# Generated by Django 5.0.7 on 2024-08-14 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('great_alliance_portal', '0002_payment_academic_year_payment_semester'),
    ]

    operations = [
        migrations.AddField(
            model_name='bursar',
            name='title',
            field=models.CharField(default='Mr.', max_length=10),
        ),
        migrations.AddField(
            model_name='staffs',
            name='title',
            field=models.CharField(default='Mr.', max_length=10),
        ),
    ]