# Generated migration for submissions deprecation
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0006_project_projectstring_alter_string_created_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='string',
            name='submission',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='submission_strings',
                to='master_data.submission',
                help_text='[DEPRECATED] Submission that generated this string. Use projects instead.'
            ),
        ),
    ]
