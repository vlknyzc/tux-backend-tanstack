import json
import logging
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from master_data.models import (
    Workspace, Field, Dimension, DimensionValue,
    Rule, RuleDetail, Platform
)

logger = logging.getLogger(__name__)


# @receiver(post_save, sender=Workspace)
# def create_fields_for_new_workspace(sender, instance, created, **kwargs):
#     if created:  # Check if this is a newly created object
#         with open('path_to_your_initial_fields.json', 'r') as file:
#             fields_data = json.load(file)

#         for field_data in fields_data:
#             Field.objects.create(
#                 platform=...,  # Assign your platform here
#                 name=field_data['name'],
#                 field_level=field_data['field_level']
#                 # ... other fields ...
#             )


class CacheInvalidationHelper:
    """Helper class for managing cache invalidation"""

    @staticmethod
    def get_cache_keys_for_rule(rule_id):
        """Get all cache keys related to a specific rule"""
        return [
            f"dimension_catalog:{rule_id}",
            f"optimized_dimension_catalog:{rule_id}",
            f"complete_rule_data:{rule_id}",
            f"field_templates:{rule_id}",
            f"inheritance_matrix:{rule_id}",
            # Django page cache key for rule configuration endpoint
            f"views.decorators.cache.cache_page.{rule_id}.GET",
        ]

    @staticmethod
    def get_rules_for_workspace(workspace):
        """Get all rule IDs in a workspace"""
        if hasattr(workspace, 'id'):
            workspace_id = workspace.id
        else:
            workspace_id = workspace
        return Rule.objects.filter(workspace_id=workspace_id).values_list('id', flat=True)

    @staticmethod
    def get_rules_for_dimension(dimension):
        """Get all rule IDs that use a specific dimension"""
        if hasattr(dimension, 'id'):
            dimension_id = dimension.id
        else:
            dimension_id = dimension
        return Rule.objects.filter(
            rule_details__dimension_id=dimension_id
        ).values_list('id', flat=True).distinct()

    @staticmethod
    def get_rules_for_platform(platform):
        """Get all rule IDs for a specific platform"""
        if hasattr(platform, 'id'):
            platform_id = platform.id
        else:
            platform_id = platform
        return Rule.objects.filter(platform_id=platform_id).values_list('id', flat=True)

    @staticmethod
    def invalidate_rule_caches(rule_ids, reason=""):
        """Invalidate all caches for given rule IDs"""
        if not rule_ids:
            return

        cache_keys_to_delete = []
        for rule_id in rule_ids:
            cache_keys_to_delete.extend(
                CacheInvalidationHelper.get_cache_keys_for_rule(rule_id)
            )

        # Debug logging
        print(f"🔥 DEBUG: Invalidating {len(cache_keys_to_delete)} cache keys for rules {list(rule_ids)}")
        print(f"🔥 DEBUG: Cache keys to delete: {cache_keys_to_delete}")

        # Delete all cache keys
        cache.delete_many(cache_keys_to_delete)

        logger.info(
            f"Invalidated caches for {len(rule_ids)} rules: {list(rule_ids)} - {reason}")

        # Also invalidate model-level caches if they exist
        for rule_id in rule_ids:
            try:
                rule = Rule.objects.get(id=rule_id)
                if hasattr(rule, 'needs_inheritance_refresh'):
                    rule.needs_inheritance_refresh = True
                    rule.save(update_fields=['needs_inheritance_refresh'])
            except Rule.DoesNotExist:
                pass


# =============================================================================
# DIMENSION VALUE SIGNALS
# =============================================================================

@receiver(post_save, sender=DimensionValue)
def invalidate_caches_on_dimension_value_save(sender, instance, created, **kwargs):
    """Invalidate caches when a dimension value is created or updated"""
    # Get all rules that use this dimension
    rule_ids = CacheInvalidationHelper.get_rules_for_dimension(
        instance.dimension)

    action = "created" if created else "updated"
    reason = f"DimensionValue {action}: {instance.dimension.name}={instance.value} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=DimensionValue)
def invalidate_caches_on_dimension_value_delete(sender, instance, **kwargs):
    """Invalidate caches when a dimension value is deleted"""
    # Get all rules that use this dimension
    rule_ids = CacheInvalidationHelper.get_rules_for_dimension(
        instance.dimension)

    reason = f"DimensionValue deleted: {instance.dimension.name}={instance.value} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


# =============================================================================
# DIMENSION SIGNALS
# =============================================================================

@receiver(post_save, sender=Dimension)
def invalidate_caches_on_dimension_save(sender, instance, created, **kwargs):
    """Invalidate caches when a dimension is created or updated"""
    # Get all rules that use this dimension
    rule_ids = CacheInvalidationHelper.get_rules_for_dimension(instance)

    action = "created" if created else "updated"
    reason = f"Dimension {action}: {instance.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=Dimension)
def invalidate_caches_on_dimension_delete(sender, instance, **kwargs):
    """Invalidate caches when a dimension is deleted"""
    # Get all rules in the same workspace (since dimension is deleted, can't query by dimension)
    rule_ids = CacheInvalidationHelper.get_rules_for_workspace(
        instance.workspace)

    reason = f"Dimension deleted: {instance.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


# =============================================================================
# RULE AND RULE DETAIL SIGNALS
# =============================================================================

@receiver(post_save, sender=Rule)
def invalidate_caches_on_rule_save(sender, instance, created, **kwargs):
    """Invalidate caches when a rule is created or updated"""
    rule_ids = [instance.id]

    action = "created" if created else "updated"
    reason = f"Rule {action}: {instance.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=Rule)
def invalidate_caches_on_rule_delete(sender, instance, **kwargs):
    """Invalidate caches when a rule is deleted"""
    rule_ids = [instance.id]

    reason = f"Rule deleted: {instance.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_save, sender=RuleDetail)
def invalidate_caches_on_rule_detail_save(sender, instance, created, **kwargs):
    """Invalidate caches when a rule detail is created or updated"""
    print(f"🔥 DEBUG: RuleDetail post_save signal triggered for {instance.id}")
    
    rule_ids = [instance.rule.id]

    action = "created" if created else "updated"
    reason = f"RuleDetail {action}: {instance.rule.name} - {instance.dimension.name} (workspace: {instance.workspace.name})"

    print(f"🔥 DEBUG: Calling invalidate_rule_caches for rule {rule_ids[0]}")
    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=RuleDetail)
def invalidate_caches_on_rule_detail_delete(sender, instance, **kwargs):
    """Invalidate caches when a rule detail is deleted"""
    rule_ids = [instance.rule.id]

    reason = f"RuleDetail deleted: {instance.rule.name} - {instance.dimension.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


# =============================================================================
# FIELD SIGNALS
# =============================================================================

@receiver(post_save, sender=Field)
def invalidate_caches_on_field_save(sender, instance, created, **kwargs):
    """Invalidate caches when a field is created or updated"""
    # Get all rules that reference this field through rule details
    rule_ids = Rule.objects.filter(
        rule_details__field=instance
    ).values_list('id', flat=True).distinct()

    action = "created" if created else "updated"
    reason = f"Field {action}: {instance.name} on platform {instance.platform.name}"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=Field)
def invalidate_caches_on_field_delete(sender, instance, **kwargs):
    """Invalidate caches when a field is deleted"""
    # Get all rules for this platform (since field is deleted, can't query by field)
    rule_ids = CacheInvalidationHelper.get_rules_for_platform(
        instance.platform)

    reason = f"Field deleted: {instance.name} on platform {instance.platform.name}"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


# =============================================================================
# PLATFORM SIGNALS
# =============================================================================

@receiver(post_save, sender=Platform)
def invalidate_caches_on_platform_save(sender, instance, created, **kwargs):
    """Invalidate caches when a platform is created or updated"""
    if not created:  # Only on updates, not creation
        rule_ids = CacheInvalidationHelper.get_rules_for_platform(instance)

        reason = f"Platform updated: {instance.name}"

        CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=Platform)
def invalidate_caches_on_platform_delete(sender, instance, **kwargs):
    """Invalidate caches when a platform is deleted"""
    # All rules for this platform should already be deleted due to CASCADE,
    # but let's clear any remaining caches just in case
    cache_keys_pattern = ["dimension_catalog:*",
                          "optimized_dimension_catalog:*", "complete_rule_data:*"]

    reason = f"Platform deleted: {instance.name}"
    logger.info(f"Platform deleted, clearing all caches - {reason}")

    # Note: Django's cache.delete_many doesn't support patterns,
    # so we'll just log this for now. In production, you might want to use
    # Redis-specific commands or a more sophisticated cache clearing strategy.


# =============================================================================
# WORKSPACE SIGNALS
# =============================================================================

@receiver(post_delete, sender=Workspace)
def invalidate_caches_on_workspace_delete(sender, instance, **kwargs):
    """Invalidate caches when a workspace is deleted"""
    # All rules for this workspace should already be deleted due to CASCADE,
    # but let's log this for monitoring
    reason = f"Workspace deleted: {instance.name}"
    logger.info(
        f"Workspace deleted, all related caches should be cleared - {reason}")
