from django.core.management.base import BaseCommand
from django.utils.text import slugify
from master_data.models import Platform, Entity

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

ENTITIES = {
    'Meta': [
        {'name': 'Business Manager', 'entity_level': 1},
        {'name': 'Account',          'entity_level': 2},
        {'name': 'Campaign',         'entity_level': 3},
        {'name': 'Ad Set',           'entity_level': 4},
        {'name': 'Ad',               'entity_level': 5},
        {'name': 'URL',              'entity_level': 6},
    ],
    'CM360': [
        {'name': 'Account', 'entity_level': 1},
        {'name': 'Advertiser', 'entity_level': 2},
        {'name': 'Campaign',   'entity_level': 3},
        {'name': 'Placement',   'entity_level': 4},
        {'name': 'Creative',         'entity_level': 5},
        {'name': 'URL',        'entity_level': 6},
    ],
    'Flashtalking': [
        {'name': 'Advertiser', 'entity_level': 1},
        {'name': 'Campaign',   'entity_level': 2},
        {'name': 'Ad Group',   'entity_level': 3},
        {'name': 'Ad',         'entity_level': 4},
        {'name': 'URL',        'entity_level': 5},
    ],

    'DV360': [
        {'name': 'Partner',         'entity_level': 1},
        {'name': 'Advertiser',      'entity_level': 2},
        {'name': 'Campaign',        'entity_level': 3},
        {'name': 'Insertion Order', 'entity_level': 4},
        {'name': 'Line Item',       'entity_level': 5},
        {'name': 'Creative',        'entity_level': 6},
        {'name': 'URL',             'entity_level': 7},
    ],

    'DV360 Trueview': [
        {'name': 'Partner',         'entity_level': 1},
        {'name': 'Advertiser',      'entity_level': 2},
        {'name': 'Insertion Order', 'entity_level': 3},
        {'name': 'Line Item',       'entity_level': 4},
        {'name': 'Youtube Ad Group', 'entity_level': 5},
        {'name': 'Youtube Ad',      'entity_level': 6},
        {'name': 'URL',             'entity_level': 7},
    ],

    'Twitter': [
        {'name': 'Business Manager', 'entity_level': 1},
        {'name': 'Account',          'entity_level': 2},
        {'name': 'Campaign',         'entity_level': 3},
        {'name': 'Ad Group',         'entity_level': 4},
        {'name': 'Ad',               'entity_level': 5},
        {'name': 'URL',              'entity_level': 6},
    ],
    'TikTok': [
        {'name': 'Advertiser', 'entity_level': 1},
        {'name': 'Campaign',   'entity_level': 2},
        {'name': 'Ad Group',   'entity_level': 3},
        {'name': 'Ad',         'entity_level': 4},
        {'name': 'URL',        'entity_level': 5},
    ],
    'Snapchat': [
        {'name': 'Advertiser', 'entity_level': 1},
        {'name': 'Campaign',   'entity_level': 2},
        {'name': 'Ad Squad',   'entity_level': 3},
        {'name': 'Ad',         'entity_level': 4},
        {'name': 'URL',        'entity_level': 5},
    ],
    'LinkedIn': [
        {'name': 'Advertiser',      'entity_level': 1},
        {'name': 'Campaign Group',  'entity_level': 2},
        {'name': 'Campaign',        'entity_level': 3},
        {'name': 'Ad',              'entity_level': 4},
        {'name': 'URL',             'entity_level': 5},
    ],
    'Pinterest': [
        {'name': 'Advertiser',      'entity_level': 1},
        {'name': 'Campaign',        'entity_level': 2},
        {'name': 'Ad Group',        'entity_level': 3},
        {'name': 'Pin Promotion',   'entity_level': 4},
        {'name': 'URL',             'entity_level': 5},
    ],
    'Reddit': [
        {'name': 'Advertiser', 'entity_level': 1},
        {'name': 'Campaign',   'entity_level': 2},
        {'name': 'Ad Group',   'entity_level': 3},
        {'name': 'Ad',         'entity_level': 4},
        {'name': 'URL',        'entity_level': 5},
    ],
    'Google Ads': [
        {'name': 'MCC',             'entity_level': 1},
        {'name': 'Account',         'entity_level': 2},
        {'name': 'Campaign',        'entity_level': 3},
        {'name': 'Ad Group',        'entity_level': 4},
        {'name': 'Ad',              'entity_level': 5},
        {'name': 'URL',             'entity_level': 6},
    ],
    'Microsoft Ads': [
        {'name': 'MCC',             'entity_level': 1},
        {'name': 'Account',         'entity_level': 2},
        {'name': 'Campaign',        'entity_level': 3},
        {'name': 'Ad Group',        'entity_level': 4},
        {'name': 'Ad',              'entity_level': 5},
        {'name': 'URL',             'entity_level': 6},
    ],

    'Amazon Ads': [
        {'name': 'Advertiser',         'entity_level': 1},
        {'name': 'Campaign',           'entity_level': 2},
        {'name': 'Ad Group',           'entity_level': 3},
        {'name': 'Sponsored Product',  'entity_level': 4},
        {'name': 'URL',                 'entity_level': 5},
    ],

    'Criteo': [
        {'name': 'Account',        'entity_level': 1},
        {'name': 'Campaign',       'entity_level': 2},
        {'name': 'Ad Set',         'entity_level': 3},
        {'name': 'Creative',       'entity_level': 4},
        {'name': 'URL',            'entity_level': 5},
    ],
    'The Trade Desk': [
        {'name': 'Advertiser',     'entity_level': 1},
        {'name': 'Campaign',       'entity_level': 2},
        {'name': 'Ad Group',       'entity_level': 3},
        {'name': 'Creative',       'entity_level': 4},
        {'name': 'URL',            'entity_level': 5},
    ],
    'Xandr': [
        {'name': 'Buyer',          'entity_level': 1},
        {'name': 'Campaign',       'entity_level': 2},
        {'name': 'Line Item',      'entity_level': 3},
        {'name': 'Creative',       'entity_level': 4},
        {'name': 'URL',            'entity_level': 5},


    ],
}


class Command(BaseCommand):
    help = 'Seed platforms and their entity hierarchies'

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

        # 2) Create/update entities
        self.stdout.write("Seeding entities…")
        created_entities = {}
        for platform_name, entity_list in ENTITIES.items():
            platform = created_platforms.get(platform_name)
            if not platform:
                self.stderr.write(
                    f"⚠️  Unknown platform {platform_name}, skipping")
                continue

            # create/update each entity
            for ed in entity_list:
                entity, created = Entity.objects.update_or_create(
                    platform=platform,
                    entity_level=ed['entity_level'],
                    defaults={'name': ed['name']},
                )
                created_entities[(platform_name, ed['entity_level'])] = entity
                if created:
                    self.stdout.write(
                        f"    Created entity: {entity.name} (Level {entity.entity_level})")

        # 3) Link next_entity pointers
        self.stdout.write("Linking next_entity relations…")
        for (platform_name, level), entity in created_entities.items():
            next_entity = created_entities.get((platform_name, level + 1))
            if next_entity and entity.next_entity_id != next_entity.id:
                entity.next_entity = next_entity
                entity.save(update_fields=['next_entity'])
                self.stdout.write(
                    f"    Linked {entity.name} -> {next_entity.name}")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
