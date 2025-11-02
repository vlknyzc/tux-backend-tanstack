# Generated manually to remove PlatformAssignment model and clean up related data

from django.db import migrations, models
import django.db.models.deletion


def delete_platform_assignment_approval_history(apps, schema_editor):
    """Delete all approval history records related to platform assignments."""
    ApprovalHistory = apps.get_model('master_data', 'ApprovalHistory')
    # Delete all approval history records that have platform_assignment set
    ApprovalHistory.objects.filter(platform_assignment__isnull=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0008_fix_projectstring_uniqueness'),
    ]

    operations = [
        # Step 1: Delete approval history records related to platform assignments
        migrations.RunPython(
            delete_platform_assignment_approval_history,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2: Remove platform_assignment field from ApprovalHistory
        migrations.RemoveField(
            model_name='approvalhistory',
            name='platform_assignment',
        ),

        # Step 3: Make project field non-nullable in ApprovalHistory
        migrations.AlterField(
            model_name='approvalhistory',
            name='project',
            field=models.ForeignKey(
                help_text='Project this approval relates to',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='approval_history',
                to='master_data.project'
            ),
        ),

        # Step 4: Remove the PlatformAssignment model and its related fields
        migrations.DeleteModel(
            name='PlatformAssignment',
        ),

        # Step 5: Remove index on ApprovalHistory for platform_assignment
        migrations.AlterModelOptions(
            name='approvalhistory',
            options={'ordering': ['-timestamp'], 'verbose_name': 'Approval History', 'verbose_name_plural': 'Approval Histories'},
        ),
    ]
