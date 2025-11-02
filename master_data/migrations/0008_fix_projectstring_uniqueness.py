# Generated manually to fix ProjectString uniqueness with NULL parent handling

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0007_make_submission_nullable"),
    ]

    operations = [
        # Remove the old unique_together constraint
        migrations.AlterUniqueTogether(
            name="projectstring",
            unique_together=set(),
        ),

        # Add two separate constraints:
        # 1. For strings WITH a parent
        migrations.AddConstraint(
            model_name='projectstring',
            constraint=models.UniqueConstraint(
                fields=['workspace', 'project', 'platform', 'field', 'parent', 'value'],
                name='unique_with_parent',
                condition=models.Q(parent__isnull=False)
            ),
        ),

        # 2. For strings WITHOUT a parent (parent=NULL)
        migrations.AddConstraint(
            model_name='projectstring',
            constraint=models.UniqueConstraint(
                fields=['workspace', 'project', 'platform', 'field', 'value'],
                name='unique_without_parent',
                condition=models.Q(parent__isnull=True)
            ),
        ),
    ]
