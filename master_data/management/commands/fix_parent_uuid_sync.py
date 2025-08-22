"""
Management command to fix parent_uuid synchronization issues.

This command identifies and fixes strings where parent_uuid doesn't match 
the parent's string_uuid, ensuring consistent parent-child relationships.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from master_data.models import String


class Command(BaseCommand):
    help = 'Fix parent_uuid synchronization issues in String model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workspace-id',
            type=int,
            help='Fix only strings in specific workspace (optional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each fix'
        )

    def handle(self, *args, **options):
        workspace_id = options.get('workspace_id')
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        # Build queryset
        queryset = String.objects.select_related('parent')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
            self.stdout.write(f"Checking strings in workspace {workspace_id}...")
        else:
            self.stdout.write("Checking all strings...")

        # Find strings with mismatched parent/parent_uuid
        mismatched_strings = []
        
        for string in queryset:
            needs_fix = False
            fix_type = None
            
            # Case 1: Has parent but parent_uuid is wrong or missing
            if string.parent and (not string.parent_uuid or string.parent_uuid != string.parent.string_uuid):
                needs_fix = True
                fix_type = 'sync_parent_uuid'
            
            # Case 2: Has parent_uuid but no parent (and parent exists)
            elif string.parent_uuid and not string.parent:
                try:
                    parent_string = String.objects.get(
                        workspace=string.workspace,
                        string_uuid=string.parent_uuid
                    )
                    needs_fix = True
                    fix_type = 'sync_parent'
                except String.DoesNotExist:
                    # Case 3: parent_uuid points to non-existent string
                    needs_fix = True
                    fix_type = 'clear_orphaned_parent_uuid'
            
            # Case 4: No parent but has parent_uuid
            elif not string.parent and string.parent_uuid:
                needs_fix = True
                fix_type = 'clear_orphaned_parent_uuid'
            
            if needs_fix:
                mismatched_strings.append({
                    'string': string,
                    'fix_type': fix_type
                })

        if not mismatched_strings:
            self.stdout.write(
                self.style.SUCCESS("✅ No parent_uuid synchronization issues found!")
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Found {len(mismatched_strings)} strings with parent_uuid synchronization issues"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE("DRY RUN - No changes will be made")
            )
        
        # Show details and fix issues
        fixed_count = 0
        
        for item in mismatched_strings:
            string = item['string']
            fix_type = item['fix_type']
            
            if verbose or dry_run:
                self.stdout.write(f"\nString ID {string.id}:")
                self.stdout.write(f"  Value: {string.value}")
                self.stdout.write(f"  Current parent: {string.parent.id if string.parent else None}")
                self.stdout.write(f"  Current parent_uuid: {string.parent_uuid}")
                self.stdout.write(f"  Fix type: {fix_type}")
            
            if not dry_run:
                try:
                    with transaction.atomic():
                        if fix_type == 'sync_parent_uuid':
                            # Set parent_uuid from parent
                            old_parent_uuid = string.parent_uuid
                            string.parent_uuid = string.parent.string_uuid
                            string.save(update_fields=['parent_uuid'])
                            
                            if verbose:
                                self.stdout.write(
                                    f"  ✅ Updated parent_uuid: {old_parent_uuid} → {string.parent_uuid}"
                                )
                        
                        elif fix_type == 'sync_parent':
                            # Set parent from parent_uuid
                            parent_string = String.objects.get(
                                workspace=string.workspace,
                                string_uuid=string.parent_uuid
                            )
                            string.parent = parent_string
                            string.save(update_fields=['parent'])
                            
                            if verbose:
                                self.stdout.write(
                                    f"  ✅ Updated parent: None → {parent_string.id}"
                                )
                        
                        elif fix_type == 'clear_orphaned_parent_uuid':
                            # Clear orphaned parent_uuid
                            old_parent_uuid = string.parent_uuid
                            string.parent_uuid = None
                            string.save(update_fields=['parent_uuid'])
                            
                            if verbose:
                                self.stdout.write(
                                    f"  ✅ Cleared orphaned parent_uuid: {old_parent_uuid} → None"
                                )
                        
                        fixed_count += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ Failed to fix string {string.id}: {str(e)}"
                        )
                    )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    f"\nDRY RUN COMPLETE: Would fix {len(mismatched_strings)} strings"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Successfully fixed {fixed_count}/{len(mismatched_strings)} strings"
                )
            )
            
            if fixed_count < len(mismatched_strings):
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  {len(mismatched_strings) - fixed_count} strings could not be fixed"
                    )
                )
