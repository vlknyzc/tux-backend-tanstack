"""
Management command to backfill missing slugs for existing records.
"""

from django.core.management.base import BaseCommand
from django.db import transaction, models

from master_data.models import Dimension, Rule, Submission, Workspace
from master_data.utils import generate_unique_slug


class Command(BaseCommand):
    help = 'Backfill missing slugs for existing records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        models_to_update = [
            (Dimension, 'name'),
            (Rule, 'name'),
            (Submission, 'name'),
            (Workspace, 'name'),
        ]

        total_updated = 0

        with transaction.atomic():
            for model_class, source_field in models_to_update:
                self.stdout.write(
                    f'\nProcessing {model_class.__name__} records...')

                # Find records with empty or null slugs
                records = model_class.objects.filter(
                    models.Q(slug__isnull=True) | models.Q(slug='')
                )

                count = records.count()
                if count == 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  No {model_class.__name__} records need slug updates')
                    )
                    continue

                self.stdout.write(
                    f'  Found {count} {model_class.__name__} records without slugs')

                updated_count = 0
                for record in records:
                    old_slug = record.slug
                    new_slug = generate_unique_slug(
                        record, source_field, 'slug', 50)

                    if not dry_run:
                        record.slug = new_slug
                        record.save(update_fields=['slug'])

                    updated_count += 1
                    self.stdout.write(
                        f'    {model_class.__name__} ID {record.id}: "{old_slug}" -> "{new_slug}"'
                    )

                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Updated {updated_count} {model_class.__name__} records')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Would update {updated_count} {model_class.__name__} records')
                    )

                total_updated += updated_count

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nDRY RUN: Would update {total_updated} total records')
                )
                # Rollback in dry-run mode
                transaction.set_rollback(True)
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully updated {total_updated} total records')
                )
