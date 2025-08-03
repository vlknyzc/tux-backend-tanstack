# Add missing created_by field to audit models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('master_data', '0006_add_missing_audit_timestamp_fields'),
    ]

    operations = [
        # Add created_by field to StringModification
        migrations.AddField(
            model_name='stringmodification',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text='User who created this record',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='master_data_stringmodification_created',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Add created_by field to StringInheritanceUpdate
        migrations.AddField(
            model_name='stringinheritanceupdate',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text='User who created this record',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='master_data_stringinheritanceupdate_created',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Add created_by field to StringUpdateBatch
        migrations.AddField(
            model_name='stringupdatebatch',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text='User who created this record',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='master_data_stringupdatebatch_created',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]