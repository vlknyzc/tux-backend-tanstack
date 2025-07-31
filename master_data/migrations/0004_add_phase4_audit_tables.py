# Generated manually for Phase 4 backend integration

from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0003_remove_workspace_from_platform_field'),
    ]

    operations = [
        # String modifications table for audit trail
        migrations.CreateModel(
            name='StringModification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('version', models.IntegerField()),
                ('field_updates', models.JSONField()),
                ('string_value', models.TextField()),
                ('original_values', models.JSONField()),
                ('modified_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('modified_at', models.DateTimeField(auto_now_add=True)),
                ('change_type', models.CharField(max_length=50)),
                ('batch_id', models.UUIDField(blank=True, null=True)),
                ('parent_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_versions', to='master_data.stringmodification')),
                ('metadata', models.JSONField(default=dict)),
                ('string', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifications', to='master_data.string')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_data.workspace')),
            ],
            options={
                'ordering': ['-modified_at'],
            },
        ),
        
        # String inheritance updates tracking
        migrations.CreateModel(
            name='StringInheritanceUpdate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('inherited_fields', models.JSONField()),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('parent_modification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inheritance_updates', to='master_data.stringmodification')),
                ('child_string', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inheritance_received', to='master_data.string')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_data.workspace')),
            ],
            options={
                'ordering': ['-applied_at'],
            },
        ),
        
        # Update batches table
        migrations.CreateModel(
            name='StringUpdateBatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('initiated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('initiated_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('total_strings', models.IntegerField()),
                ('processed_strings', models.IntegerField(default=0)),
                ('failed_strings', models.IntegerField(default=0)),
                ('backup_id', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(default=dict)),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_data.workspace')),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_data.rule')),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_data.field')),
            ],
            options={
                'ordering': ['-initiated_at'],
            },
        ),
        
        # Add version field to String model
        migrations.AddField(
            model_name='string',
            name='version',
            field=models.IntegerField(default=1),
        ),
        
        # Add indexes for performance
        migrations.RunSQL(
            "CREATE INDEX idx_string_modifications_string_id ON master_data_stringmodification(string_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_string_modifications_string_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_string_modifications_batch_id ON master_data_stringmodification(batch_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_string_modifications_batch_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_string_modifications_modified_at ON master_data_stringmodification(modified_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_string_modifications_modified_at;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_inheritance_updates_parent ON master_data_stringinheritanceupdate(parent_modification_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_inheritance_updates_parent;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_inheritance_updates_child ON master_data_stringinheritanceupdate(child_string_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_inheritance_updates_child;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_update_batches_workspace ON master_data_stringupdatebatch(workspace_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_update_batches_workspace;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_update_batches_status ON master_data_stringupdatebatch(status);",
            reverse_sql="DROP INDEX IF EXISTS idx_update_batches_status;"
        ),
        
        # Add unique constraint for string version tracking
        migrations.AddConstraint(
            model_name='stringmodification',
            constraint=models.UniqueConstraint(fields=['string', 'version'], name='unique_string_version'),
        ),
        migrations.AddConstraint(
            model_name='stringinheritanceupdate',
            constraint=models.UniqueConstraint(fields=['parent_modification', 'child_string'], name='unique_inheritance_update'),
        ),
    ]