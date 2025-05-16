from django.core.management.base import BaseCommand
from master_data.models import Platform, Field

PLATFORMS = [
    {'platform_type': 'social_media', 'name': 'Meta'},
    {'platform_type': 'DSP',          'name': 'DV360'},
]

FIELDS = {
    'Meta': [
        {'name': 'Business Manager', 'field_level': 1},
        {'name': 'Account',          'field_level': 2},
        {'name': 'Campaign',         'field_level': 3},
        {'name': 'Ad Set',           'field_level': 4},
        {'name': 'Ad',               'field_level': 5},
    ],
    'DV360': [
        {'name': 'Partner',         'field_level': 1},
        {'name': 'Campaign',        'field_level': 2},
        {'name': 'Insertion Order', 'field_level': 3},
        {'name': 'Line Item',       'field_level': 4},
        {'name': 'Creative',        'field_level': 5},
    ],
}


class Command(BaseCommand):
    help = 'Seed platforms and their field hierarchies'

    def handle(self, *args, **options):
        # 1) Create or update platforms
        self.stdout.write("Seeding platforms…")
        created_platforms = {}
        for pdata in PLATFORMS:
            platform, _ = Platform.objects.update_or_create(
                platform_type=pdata['platform_type'],
                name=pdata['name'],
                defaults=pdata
            )
            created_platforms[platform.name] = platform

        # 2) Create/update fields
        self.stdout.write("Seeding fields…")
        created_fields = {}
        for platform_name, field_list in FIELDS.items():
            platform = created_platforms.get(platform_name)
            if not platform:
                self.stderr.write(
                    f"⚠️  Unknown platform {platform_name}, skipping")
                continue

            # create/update each field
            for fd in field_list:
                field, _ = Field.objects.update_or_create(
                    platform=platform,
                    field_level=fd['field_level'],
                    defaults={'name': fd['name']},
                )
                created_fields[(platform_name, fd['field_level'])] = field

        # 3) Link next_field pointers
        self.stdout.write("Linking next_field relations…")
        for (platform_name, level), field in created_fields.items():
            next_field = created_fields.get((platform_name, level + 1))
            if next_field and field.next_field_id != next_field.id:
                field.next_field = next_field
                field.save(update_fields=['next_field'])

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
