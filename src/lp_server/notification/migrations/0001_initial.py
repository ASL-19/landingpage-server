# Generated by Django 3.2.24 on 2024-03-26 20:04

import ckeditor_uploader.fields
from django.db import migrations, models
import django.db.models.deletion
import notification.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('distribution', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationBroadcast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('purpose', models.CharField(help_text='Used for differentiating between broadcasts (e.g. Testing TG notifications internally)', max_length=75)),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('SCHEDULED', 'SCHEDULED'), ('SENT', 'SENT'), ('INCOMPLETE', 'INCOMPLETE'), ('INPROGRESS', 'IN PROGRESS'), ('FAILED', 'FAILED')], default='PENDING', editable=False, max_length=10, verbose_name='Status')),
                ('subject', models.CharField(max_length=75)),
                ('body', ckeditor_uploader.fields.RichTextUploadingField()),
                ('parser_type', models.CharField(choices=[('TEXT', 'TEXT'), ('HTML', 'HTML'), ('MARKDOWN', 'MARKDOWN')], default='HTML', max_length=8, verbose_name='Body Type')),
                ('deadline', models.DateTimeField(default=notification.models.get_deadline, verbose_name='Deadline')),
                ('scheduled', models.DateTimeField(blank=True, null=True, verbose_name='Scheduled on')),
                ('action', models.CharField(choices=[('NOTIFY', 'Notify VPN users'), ('DEACTIVATE', 'Deactivate keys')], default='NOTIFY', max_length=10, verbose_name='Action')),
            ],
            options={
                'verbose_name': 'Notification Broadcast',
                'verbose_name_plural': 'Notifications Broadcasts',
                'db_table': 'distribution_notificationbroadcast',
            },
        ),
        migrations.CreateModel(
            name='NotificationBroadcastConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bc_purpose', models.CharField(help_text='Used for differentiating between broadcasts (e.g. Testing TG notifications internally)', max_length=75, verbose_name='Broadcast purpose')),
                ('notification_subject', models.CharField(max_length=75)),
                ('notification_body', ckeditor_uploader.fields.RichTextUploadingField()),
                ('parser_type', models.CharField(choices=[('TEXT', 'TEXT'), ('HTML', 'HTML'), ('MARKDOWN', 'MARKDOWN')], default='HTML', max_length=8, verbose_name='Body Type')),
            ],
            options={
                'verbose_name': 'Notification Broadcast Configuration',
            },
        ),
        migrations.CreateModel(
            name='NotificationMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('SCHEDULED', 'SCHEDULED'), ('SENT', 'SENT'), ('OPTEDOUT', 'OPTED OUT'), ('FAILED', 'FAILED')], default='PENDING', editable=False, max_length=10, verbose_name='Status')),
                ('attempts', models.IntegerField(default=0, verbose_name='Number of attempts')),
                ('sent', models.DateTimeField(blank=True, null=True, verbose_name='Sent on')),
                ('error_msg', models.TextField(default='N/A')),
                ('broadcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='notification.notificationbroadcast')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='distribution.vpnuser')),
            ],
            options={
                'verbose_name': 'Notification Message',
                'verbose_name_plural': 'Notifications Messages',
                'db_table': 'distribution_notificationmessage',
            },
        ),
        migrations.AddField(
            model_name='notificationbroadcast',
            name='recipients',
            field=models.ManyToManyField(through='notification.NotificationMessage', to='distribution.Vpnuser'),
        ),
    ]
