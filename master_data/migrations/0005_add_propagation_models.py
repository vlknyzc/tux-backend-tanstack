# Generated manually for propagation models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0004_add_phase4_audit_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropagationJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='When this record was created')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='When this record was last updated')),
                ('batch_id', models.UUIDField(default=uuid.uuid4, help_text='Unique identifier for this propagation batch', unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('partial_failure', 'Partial Failure')], default='pending', help_text='Current status of the propagation job', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, help_text='When the job actually started processing', null=True)),
                ('completed_at', models.DateTimeField(blank=True, help_text='When the job completed or failed', null=True)),
                ('total_strings', models.PositiveIntegerField(default=0, help_text='Total number of strings to be processed')),
                ('processed_strings', models.PositiveIntegerField(default=0, help_text='Number of strings successfully processed')),
                ('failed_strings', models.PositiveIntegerField(default=0, help_text='Number of strings that failed processing')),
                ('max_depth', models.PositiveIntegerField(default=10, help_text='Maximum propagation depth configured for this job')),
                ('processing_method', models.CharField(choices=[('synchronous', 'Synchronous'), ('background', 'Background'), ('chunked', 'Chunked Processing')], default='synchronous', help_text='Processing method used for this job', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about the job configuration and execution')),
                ('error_message', models.TextField(blank=True, help_text='Error message if job failed', null=True)),
                ('triggered_by', models.ForeignKey(help_text='User who triggered this propagation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='triggered_propagation_jobs', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(help_text='Workspace this record belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='propagation_jobs', to='master_data.workspace')),
            ],
            options={
                'verbose_name': 'Propagation Job',
                'verbose_name_plural': 'Propagation Jobs',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='PropagationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='When this record was created')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='When this record was last updated')),
                ('settings', models.JSONField(default=dict, help_text='User-specific propagation settings')),
                ('user', models.ForeignKey(help_text='User these settings belong to', on_delete=django.db.models.deletion.CASCADE, related_name='propagation_settings', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(help_text='Workspace this record belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='propagation_settings', to='master_data.workspace')),
            ],
            options={
                'verbose_name': 'Propagation Settings',
                'verbose_name_plural': 'Propagation Settings',
            },
        ),
        migrations.CreateModel(
            name='PropagationError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='When this record was created')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='When this record was last updated')),
                ('error_type', models.CharField(choices=[('string_generation_error', 'String Generation Error'), ('database_error', 'Database Error'), ('validation_error', 'Validation Error'), ('circular_dependency', 'Circular Dependency'), ('conflict_error', 'Conflict Error'), ('permission_error', 'Permission Error'), ('timeout_error', 'Timeout Error'), ('unknown_error', 'Unknown Error')], help_text='Type of error that occurred', max_length=30)),
                ('error_message', models.TextField(help_text='Human-readable error message')),
                ('error_code', models.CharField(blank=True, help_text='Machine-readable error code', max_length=50, null=True)),
                ('stack_trace', models.TextField(blank=True, help_text='Full stack trace of the error', null=True)),
                ('context_data', models.JSONField(blank=True, default=dict, help_text='Additional context data about the error')),
                ('retry_count', models.PositiveIntegerField(default=0, help_text='Number of times this operation has been retried')),
                ('is_retryable', models.BooleanField(default=False, help_text='Whether this error can be retried')),
                ('resolved', models.BooleanField(default=False, help_text='Whether this error has been resolved')),
                ('resolved_at', models.DateTimeField(blank=True, help_text='When this error was resolved', null=True)),
                ('job', models.ForeignKey(help_text='Propagation job this error belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='errors', to='master_data.propagationjob')),
                ('resolved_by', models.ForeignKey(blank=True, help_text='User who resolved this error', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_propagation_errors', to=settings.AUTH_USER_MODEL)),
                ('string', models.ForeignKey(blank=True, help_text='String that caused the error (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='propagation_errors', to='master_data.string')),
                ('string_detail', models.ForeignKey(blank=True, help_text='StringDetail that caused the error (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='propagation_errors', to='master_data.stringdetail')),
                ('workspace', models.ForeignKey(help_text='Workspace this record belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='propagation_errors', to='master_data.workspace')),
            ],
            options={
                'verbose_name': 'Propagation Error',
                'verbose_name_plural': 'Propagation Errors',
                'ordering': ['-created'],
            },
        ),
        migrations.AddIndex(
            model_name='propagationsettings',
            index=models.Index(fields=['workspace', 'user'], name='master_data_propagat_userworkspace_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='propagationsettings',
            unique_together={('user', 'workspace')},
        ),
        migrations.AddIndex(
            model_name='propagationjob',
            index=models.Index(fields=['workspace', 'status'], name='master_data_propagat_workspace_status_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationjob',
            index=models.Index(fields=['workspace', 'triggered_by'], name='master_data_propagat_workspace_user_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationjob',
            index=models.Index(fields=['batch_id'], name='master_data_propagat_batch_id_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationjob',
            index=models.Index(fields=['created'], name='master_data_propagat_created_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationerror',
            index=models.Index(fields=['workspace', 'error_type'], name='master_data_propagat_workspace_error_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationerror',
            index=models.Index(fields=['workspace', 'resolved'], name='master_data_propagat_workspace_resolved_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationerror',
            index=models.Index(fields=['job', 'error_type'], name='master_data_propagat_job_error_idx'),
        ),
        migrations.AddIndex(
            model_name='propagationerror',
            index=models.Index(fields=['created'], name='master_data_propagat_error_created_idx'),
        ),
    ]