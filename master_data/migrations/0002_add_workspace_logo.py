from django.db import migrations, models


def default_workspace_logo():
    return "workspaces/default/default-workspace-logo.png"


class Migration(migrations.Migration):

    dependencies = [
        # Make sure this points to your last migration
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workspace',
            name='logo',
            field=models.ImageField(
                blank=True, default=default_workspace_logo, null=True, upload_to='workspaces/logos/'),
        ),
    ]
