# Generated by Django 3.2.24 on 2024-03-26 20:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('preference', '0001_initial'),
        ('server', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountDeleteReason',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('description_en', models.TextField(null=True)),
                ('description_fa', models.TextField(null=True)),
                ('description_ar', models.TextField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=128)),
                ('description', models.CharField(max_length=256)),
                ('description_en', models.CharField(max_length=256, null=True)),
                ('description_fa', models.CharField(max_length=256, null=True)),
                ('description_ar', models.CharField(max_length=256, null=True)),
            ],
            options={
                'ordering': ['-id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Prefix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('port', models.IntegerField(blank=True, null=True)),
                ('prefix_str', models.CharField(max_length=256)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Prefixes',
            },
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('servers', models.IntegerField()),
                ('countries', models.IntegerField()),
                ('downloads', models.IntegerField()),
                ('active_monthly_users', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Vpnuser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(max_length=256, unique=True)),
                ('channel', models.CharField(choices=[('TG', 'Telegram'), ('EM', 'Email'), ('SG', 'Signal'), ('NA', 'Unknown')], default='NA', max_length=2)),
                ('reputation', models.IntegerField(default=0)),
                ('delete_date', models.DateTimeField(blank=True, null=True)),
                ('banned', models.BooleanField(default=False)),
                ('banned_reason', models.IntegerField(choices=[(0, 'Not banned'), (1, 'Account Deleted'), (2, 'Account Shared'), (3, 'Admin Banned'), (4, 'API Update'), (5, 'Torrent')], default=0)),
                ('userchat', models.CharField(blank=True, max_length=256, null=True)),
                ('notification_status', models.CharField(choices=[('ENABLED', 'ENABLED'), ('BLOCKED_BOT', 'BLOCKED BOT'), ('ACCOUNT_DEACTIVATED', 'ACCOUNT DEACTIVATED')], default='ENABLED', help_text='if the telegram bot is blocked or the telegram User account is deactivated', max_length=25, verbose_name='Notification Status')),
                ('delete_reason', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='distribution.accountdeletereason')),
                ('region', models.ManyToManyField(blank=True, to='preference.Region')),
            ],
            options={
                'ordering': ['-id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OutlineUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('outline_key_id', models.IntegerField()),
                ('outline_key', models.CharField(max_length=512)),
                ('reputation', models.IntegerField(default=0)),
                ('transfer', models.FloatField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('removed', models.BooleanField(default=False)),
                ('exists_on_server', models.BooleanField(default=True)),
                ('group_id', models.BigIntegerField(blank=True, null=True)),
                ('delete_date', models.DateTimeField(blank=True, null=True)),
                ('deletion_cause', models.CharField(choices=[('NA', 'Not applicable'), ('INACTIVE', 'Inactive Key Removal')], default='NA', editable=False, max_length=10, verbose_name='Deletion Cause')),
                ('request_type', models.CharField(default='legacy', editable=False, max_length=128, verbose_name='Request Type')),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='users', to='server.outlineserver')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='outline_keys', to='distribution.vpnuser')),
                ('user_issue', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='distribution.issue')),
            ],
            options={
                'verbose_name': 'OutlineUser',
                'verbose_name_plural': 'OutlineUsers',
            },
        ),
        migrations.CreateModel(
            name='OnlineConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('file_name', models.CharField(blank=True, max_length=256, null=True, unique=True)),
                ('storage_service', models.CharField(blank=True, max_length=64, null=True)),
                ('outline_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='online_configs', to='distribution.outlineuser')),
            ],
            options={
                'ordering': ['-id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LoadBalancer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_name', models.CharField(max_length=128)),
                ('is_active', models.BooleanField(default=True)),
                ('replaces_ip', models.BooleanField(default=True, help_text="Doesn't apply to gtf servers")),
                ('server', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='server.outlineserver')),
            ],
            options={
                'verbose_name_plural': 'Load Balancers',
            },
        ),
    ]