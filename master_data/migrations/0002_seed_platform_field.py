from django.db import migrations


def create_initial_data(apps, schema_editor):
    Platform = apps.get_model('master_data', 'Platform')
    Field = apps.get_model('master_data', 'Field')

    # Create platforms
    platforms_data = [
        {
            'platform_type': 'social_media',
            'name': 'Meta'
        },
        {
            'platform_type': 'social_media',
            'name': 'DV360'
        }
    ]

    created_platforms = {}
    for platform_data in platforms_data:
        platform = Platform.objects.create(**platform_data)
        created_platforms[platform.name] = platform

    # Create fields for each platform
    fields_data = {
        'Meta': [
            {'name': 'Business Manager', 'field_level': 1},
            {'name': 'Account', 'field_level': 2},
            {'name': 'Campaign', 'field_level': 3},
            {'name': 'Ad Set', 'field_level': 4},
            {'name': 'Ad', 'field_level': 5},
        ],
        'DV360': [
            {'name': 'Partner', 'field_level': 1},
            {'name': 'Campaign', 'field_level': 2},
            {'name': 'Insertion Order', 'field_level': 3},
            {'name': 'Line Item', 'field_level': 4},
            {'name': 'Creative', 'field_level': 5},
        ]
    }

    # Create fields and set up next_field relationships
    for platform_name, fields in fields_data.items():
        platform = created_platforms[platform_name]
        previous_field = None

        for field_data in fields:
            field = Field.objects.create(
                platform=platform,
                name=field_data['name'],
                field_level=field_data['field_level'],
                next_field=previous_field
            )
            previous_field = field


def reverse_initial_data(apps, schema_editor):
    Platform = apps.get_model('master_data', 'Platform')
    Field = apps.get_model('master_data', 'Field')

    # Delete all fields first (due to foreign key relationship)
    Field.objects.all().delete()
    # Then delete all platforms
    Platform.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]
