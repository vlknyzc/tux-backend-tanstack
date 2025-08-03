# Add missing timestamp fields to audit models

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0005_add_propagation_models'),
    ]

    operations = [
        # Add created field to StringModification
        migrations.AddField(
            model_name='stringmodification',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Add last_updated field to StringModification  
        migrations.AddField(
            model_name='stringmodification',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add created field to StringInheritanceUpdate
        migrations.AddField(
            model_name='stringinheritanceupdate',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Add last_updated field to StringInheritanceUpdate
        migrations.AddField(
            model_name='stringinheritanceupdate',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Add created field to StringUpdateBatch
        migrations.AddField(
            model_name='stringupdatebatch',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Add last_updated field to StringUpdateBatch
        migrations.AddField(
            model_name='stringupdatebatch',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]