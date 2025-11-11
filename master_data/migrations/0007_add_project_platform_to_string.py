# Generated manually to add project and platform fields to String model
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0006_rename_projectstring_to_string"),
    ]

    operations = [
        # Add new fields to String
        migrations.AddField(
            model_name='string',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='strings',
                to='master_data.project',
                help_text='Project this string belongs to',
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='string',
            name='platform',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='strings',
                to='master_data.platform',
                help_text='Platform this string belongs to (via project platform assignment)',
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='string',
            name='last_synced_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='Last sync with external platform',
            ),
        ),
        migrations.AddField(
            model_name='string',
            name='sync_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('in_sync', 'In Sync'),
                    ('out_of_sync', 'Out of Sync'),
                    ('conflict', 'Conflict'),
                ],
                null=True,
                blank=True,
                help_text='Sync status with external platform',
            ),
        ),
        migrations.AddField(
            model_name='string',
            name='source_external_string',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='imported_strings',
                to='master_data.externalstring',
                help_text='Source ExternalString if imported from validation',
            ),
        ),

        # Add is_inherited to StringDetail
        migrations.AddField(
            model_name='stringdetail',
            name='is_inherited',
            field=models.BooleanField(
                default=False,
                help_text='Whether this value was inherited from parent string',
            ),
        ),

        # Remove old fields from String
        migrations.RemoveField(
            model_name='string',
            name='generation_metadata',
        ),
        migrations.RemoveField(
            model_name='string',
            name='is_auto_generated',
        ),
        migrations.RemoveField(
            model_name='string',
            name='submission',
        ),
        migrations.RemoveField(
            model_name='string',
            name='validation_status',
        ),
        migrations.RemoveField(
            model_name='string',
            name='version',
        ),

        # Update indexes
        migrations.AlterModelOptions(
            name='string',
            options={
                'ordering': ['workspace', 'project', 'entity__entity_level', 'value'],
                'verbose_name': 'String',
                'verbose_name_plural': 'Strings',
            },
        ),

        # Remove old indexes/constraints (only those that exist)
        migrations.RemoveIndex(
            model_name='string',
            name='master_data_workspa_6947b4_idx',
        ),
        migrations.RemoveIndex(
            model_name='string',
            name='master_data_validat_c825ae_idx',
        ),
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS unique_external_platform_id_per_workspace CASCADE;",
            reverse_sql="",  # We'll recreate it differently below
        ),

        # Add new indexes
        migrations.AddIndex(
            model_name='string',
            index=models.Index(
                fields=['workspace', 'project', 'platform'],
                name='master_data_workspa_e05d12_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='string',
            index=models.Index(
                fields=['workspace', 'parent_uuid'],
                name='master_data_workspa_888a84_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='string',
            index=models.Index(
                fields=['project', 'platform', 'entity'],
                name='master_data_project_398590_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='string',
            index=models.Index(
                fields=['validation_source', 'sync_status'],
                name='master_data_validat_387643_idx',
            ),
        ),

        # Add new indexes to StringDetail
        migrations.AddIndex(
            model_name='stringdetail',
            index=models.Index(
                fields=['string', 'dimension'],
                name='master_data_string__9500ee_idx',
            ),
        ),

        # Add new constraints
        migrations.AddConstraint(
            model_name='string',
            constraint=models.UniqueConstraint(
                fields=['workspace', 'project', 'platform', 'entity', 'parent', 'value'],
                name='unique_with_parent',
                condition=models.Q(parent__isnull=False),
            ),
        ),
        migrations.AddConstraint(
            model_name='string',
            constraint=models.UniqueConstraint(
                fields=['workspace', 'project', 'platform', 'entity', 'value'],
                name='unique_without_parent',
                condition=models.Q(parent__isnull=True),
            ),
        ),
        migrations.AddConstraint(
            model_name='string',
            constraint=models.UniqueConstraint(
                fields=['workspace', 'external_platform_id'],
                condition=models.Q(
                    external_platform_id__isnull=False,
                    validation_source='external',
                ),
                name='unique_project_string_external_id',
            ),
        ),
    ]
