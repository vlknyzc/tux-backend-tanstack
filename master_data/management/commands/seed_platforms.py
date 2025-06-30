from django.core.management.base import BaseCommand
from django.utils.text import slugify
from master_data.models import Platform, Field

PLATFORMS = [
    {'platform_type': 'social_media', 'name': 'Meta',
        'slug': 'meta',               'icon_name': 'meta'},
    {'platform_type': 'DSP',          'name': 'DV360',
        'slug': 'dv360',              'icon_name': 'googledisplayandvideo360'},
    {'platform_type': 'DSP',          'name': 'DV360 Trueview',
        'slug': 'dv360-trueview',    'icon_name': 'googledisplayandvideo360'},
    {'platform_type': 'Adserver',          'name': 'Flashtalking',
        'slug': 'flashtalking',      'icon_name': 'flashtalking'},
    {'platform_type': 'Adserver',          'name': 'CM360',
        'slug': 'cm360',              'icon_name': 'cm360'},
    {'platform_type': 'social_media', 'name': 'Twitter',
        'slug': 'twitter',            'icon_name': 'x'},  # Twitter is now X
    {'platform_type': 'social_media', 'name': 'TikTok',
        'slug': 'tiktok',             'icon_name': 'tiktok'},
    {'platform_type': 'social_media', 'name': 'Snapchat',
        'slug': 'snapchat',           'icon_name': 'snapchat'},
    {'platform_type': 'social_media', 'name': 'LinkedIn',
        'slug': 'linkedin',           'icon_name': 'linkedin'},
    {'platform_type': 'social_media', 'name': 'Pinterest',
        'slug': 'pinterest',          'icon_name': 'pinterest'},
    {'platform_type': 'social_media', 'name': 'Reddit',
        'slug': 'reddit',             'icon_name': 'reddit'},
    {'platform_type': 'search',       'name': 'Google Ads',
        'slug': 'google-ads',         'icon_name': 'googleads'},
    {'platform_type': 'search',       'name': 'Microsoft Ads',
        'slug': 'microsoft-ads',      'icon_name': 'microsoftadvertising'},
    {'platform_type': 'video',        'name': 'YouTube',
        'slug': 'youtube',            'icon_name': 'youtube'},
    {'platform_type': 'retail_media', 'name': 'Amazon Ads',
        'slug': 'amazon-ads',         'icon_name': 'amazons'},
    {'platform_type': 'retail_media', 'name': 'Walmart Connect',
        'slug': 'walmart-connect',    'icon_name': None},  # not in Simple Icons
    {'platform_type': 'retail_media', 'name': 'Criteo',
        'slug': 'criteo',             'icon_name': None},  # not in Simple Icons
    {'platform_type': 'DSP',          'name': 'The Trade Desk',
        'slug': 'the-trade-desk',     'icon_name': None},  # not in Simple Icons
    {'platform_type': 'DSP',          'name': 'Xandr',
        'slug': 'xandr',              'icon_name': None},  # not in Simple Icons
]

FIELDS = {
    'Meta': [
        {'name': 'Business Manager', 'field_level': 1},
        {'name': 'Account',          'field_level': 2},
        {'name': 'Campaign',         'field_level': 3},
        {'name': 'Ad Set',           'field_level': 4},
        {'name': 'Ad',               'field_level': 5},
        {'name': 'URL',              'field_level': 6},
    ],
    'CM360': [
        {'name': 'Advertiser', 'field_level': 1},
        {'name': 'Campaign',   'field_level': 2},
        {'name': 'Ad Group',   'field_level': 3},
        {'name': 'Ad',         'field_level': 4},
        {'name': 'URL',        'field_level': 5},
    ],
    'Flashtalking': [
        {'name': 'Advertiser', 'field_level': 1},
        {'name': 'Campaign',   'field_level': 2},
        {'name': 'Ad Group',   'field_level': 3},
        {'name': 'Ad',         'field_level': 4},
        {'name': 'URL',        'field_level': 5},
    ],

    'DV360': [
        {'name': 'Partner',         'field_level': 1},
        {'name': 'Advertiser',      'field_level': 2},
        {'name': 'Campaign',        'field_level': 3},
        {'name': 'Insertion Order', 'field_level': 4},
        {'name': 'Line Item',       'field_level': 5},
        {'name': 'Creative',        'field_level': 6},
        {'name': 'URL',             'field_level': 7},
    ],

    'DV360 Trueview': [
        {'name': 'Partner',         'field_level': 1},
        {'name': 'Advertiser',      'field_level': 2},
        {'name': 'Insertion Order', 'field_level': 3},
        {'name': 'Line Item',       'field_level': 4},
        {'name': 'Youtube Ad Group', 'field_level': 5},
        {'name': 'Youtube Ad',      'field_level': 6},
        {'name': 'URL',             'field_level': 7},
    ],

    'Twitter': [
        {'name': 'Business Manager', 'field_level': 1},
        {'name': 'Account',          'field_level': 2},
        {'name': 'Campaign',         'field_level': 3},
        {'name': 'Ad Group',         'field_level': 4},
        {'name': 'Ad',               'field_level': 5},
        {'name': 'URL',              'field_level': 6},
    ],
    'TikTok': [
        {'name': 'Advertiser', 'field_level': 1},
        {'name': 'Campaign',   'field_level': 2},
        {'name': 'Ad Group',   'field_level': 3},
        {'name': 'Ad',         'field_level': 4},
        {'name': 'URL',        'field_level': 5},
    ],
    'Snapchat': [
        {'name': 'Advertiser', 'field_level': 1},
        {'name': 'Campaign',   'field_level': 2},
        {'name': 'Ad Squad',   'field_level': 3},
        {'name': 'Ad',         'field_level': 4},
        {'name': 'URL',        'field_level': 5},
    ],
    'LinkedIn': [
        {'name': 'Advertiser',      'field_level': 1},
        {'name': 'Campaign Group',  'field_level': 2},
        {'name': 'Campaign',        'field_level': 3},
        {'name': 'Ad',              'field_level': 4},
        {'name': 'URL',             'field_level': 5},
    ],
    'Pinterest': [
        {'name': 'Advertiser',      'field_level': 1},
        {'name': 'Campaign',        'field_level': 2},
        {'name': 'Ad Group',        'field_level': 3},
        {'name': 'Pin Promotion',   'field_level': 4},
        {'name': 'URL',             'field_level': 5},
    ],
    'Reddit': [
        {'name': 'Advertiser', 'field_level': 1},
        {'name': 'Campaign',   'field_level': 2},
        {'name': 'Ad Group',   'field_level': 3},
        {'name': 'Ad',         'field_level': 4},
        {'name': 'URL',        'field_level': 5},
    ],
    'Google Ads': [
        {'name': 'MCC',             'field_level': 1},
        {'name': 'Account',         'field_level': 2},
        {'name': 'Campaign',        'field_level': 3},
        {'name': 'Ad Group',        'field_level': 4},
        {'name': 'Ad',              'field_level': 5},
        {'name': 'URL',             'field_level': 6},
    ],
    'Microsoft Ads': [
        {'name': 'MCC',             'field_level': 1},
        {'name': 'Account',         'field_level': 2},
        {'name': 'Campaign',        'field_level': 3},
        {'name': 'Ad Group',        'field_level': 4},
        {'name': 'Ad',              'field_level': 5},
        {'name': 'URL',             'field_level': 6},
    ],

    'Amazon Ads': [
        {'name': 'Advertiser',         'field_level': 1},
        {'name': 'Campaign',           'field_level': 2},
        {'name': 'Ad Group',           'field_level': 3},
        {'name': 'Sponsored Product',  'field_level': 4},
        {'name': 'URL',                 'field_level': 5},
    ],

    'Criteo': [
        {'name': 'Account',        'field_level': 1},
        {'name': 'Campaign',       'field_level': 2},
        {'name': 'Ad Set',         'field_level': 3},
        {'name': 'Creative',       'field_level': 4},
        {'name': 'URL',            'field_level': 5},
    ],
    'The Trade Desk': [
        {'name': 'Advertiser',     'field_level': 1},
        {'name': 'Campaign',       'field_level': 2},
        {'name': 'Ad Group',       'field_level': 3},
        {'name': 'Creative',       'field_level': 4},
        {'name': 'URL',            'field_level': 5},
    ],
    'Xandr': [
        {'name': 'Buyer',          'field_level': 1},
        {'name': 'Campaign',       'field_level': 2},
        {'name': 'Line Item',      'field_level': 3},
        {'name': 'Creative',       'field_level': 4},
        {'name': 'URL',            'field_level': 5},


    ],
}


class Command(BaseCommand):
    help = 'Seed platforms and their field hierarchies'

    def handle(self, *args, **options):
        # 1) Create or update platforms
        self.stdout.write("Seeding platforms…")
        created_platforms = {}
        for pdata in PLATFORMS:
            platform, created = Platform.objects.update_or_create(
                platform_type=pdata['platform_type'],
                name=pdata['name'],
                defaults={
                    'platform_type': pdata['platform_type'],
                    'icon_name': pdata.get('icon_name'),
                    'slug': pdata.get('slug')
                }
            )
            created_platforms[platform.name] = platform
            if created:
                self.stdout.write(f"  Created platform: {platform.name}")
            else:
                self.stdout.write(f"  Updated platform: {platform.name}")

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
                field, created = Field.objects.update_or_create(
                    platform=platform,
                    field_level=fd['field_level'],
                    defaults={'name': fd['name']},
                )
                created_fields[(platform_name, fd['field_level'])] = field
                if created:
                    self.stdout.write(
                        f"    Created field: {field.name} (Level {field.field_level})")

        # 3) Link next_field pointers
        self.stdout.write("Linking next_field relations…")
        for (platform_name, level), field in created_fields.items():
            next_field = created_fields.get((platform_name, level + 1))
            if next_field and field.next_field_id != next_field.id:
                field.next_field = next_field
                field.save(update_fields=['next_field'])
                self.stdout.write(
                    f"    Linked {field.name} -> {next_field.name}")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
