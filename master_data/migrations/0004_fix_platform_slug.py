# Generated manually to fix deployment issue with slug constraint

from django.db import migrations, models
from django.utils.text import slugify
from django.db.utils import IntegrityError


def ensure_unique_slugs(apps, schema_editor):
    """
    Ensure all Platform instances have unique slugs
    """
    Platform = apps.get_model('master_data', 'Platform')

    # Get all platforms
    platforms = Platform.objects.all()
    used_slugs = set()

    for platform in platforms:
        if not platform.slug:
            base_slug = slugify(platform.name)
        else:
            base_slug = platform.slug

        # Ensure uniqueness
        slug = base_slug
        counter = 1
        while slug in used_slugs or Platform.objects.filter(slug=slug).exclude(pk=platform.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        platform.slug = slug
        used_slugs.add(slug)
        platform.save(update_fields=['slug'])


def reverse_ensure_unique_slugs(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0003_add_platform_slug"),
    ]

    operations = [
        migrations.RunPython(ensure_unique_slugs, reverse_ensure_unique_slugs),
    ]
