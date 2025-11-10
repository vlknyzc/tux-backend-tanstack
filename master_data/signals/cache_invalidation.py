"""
Cache invalidation signal handlers for master_data app.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from ..models import Rule, RuleDetail, DimensionValue, DimensionConstraint, Entity, Platform, Workspace

logger = logging.getLogger(__name__)


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
            # Try multiple possible formats
            f"views.decorators.cache.cache_page.GET.rule_id.{rule_id}.configuration",
            f"views.decorators.cache.cache_page.{rule_id}.GET",
            f"views.decorators.cache.cache_page.GET.rule_id.{rule_id}",
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

        # Log cache invalidation for monitoring
        logger.info(
            f"Invalidating {len(cache_keys_to_delete)} cache keys for rules {list(rule_ids)}")
        logger.info(f"Cache keys to delete: {cache_keys_to_delete}")

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
# RULE DETAIL SIGNALS
# =============================================================================

@receiver(post_save, sender=RuleDetail)
def invalidate_caches_on_rule_detail_save(sender, instance, created, **kwargs):
    """Invalidate caches when a rule detail is created or updated"""
    rule_ids = [instance.rule.id]

    action = "created" if created else "updated"
    reason = f"RuleDetail {action}: {instance.rule.name} - {instance.dimension.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=RuleDetail)
def invalidate_caches_on_rule_detail_delete(sender, instance, **kwargs):
    """Invalidate caches when a rule detail is deleted"""
    rule_ids = [instance.rule.id]

    reason = f"RuleDetail deleted: {instance.rule.name} - {instance.dimension.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


# =============================================================================
# RULE SIGNALS
# =============================================================================

@receiver(post_save, sender=Rule)
def invalidate_caches_on_rule_save(sender, instance, created, **kwargs):
    """Invalidate caches when a rule is created or updated"""
    if not created:  # Only on updates, not creation
        rule_ids = [instance.id]

        reason = f"Rule updated: {instance.name} (workspace: {instance.workspace.name})"

        CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


@receiver(post_delete, sender=Rule)
def invalidate_caches_on_rule_delete(sender, instance, **kwargs):
    """Invalidate caches when a rule is deleted"""
    rule_ids = [instance.id]

    reason = f"Rule deleted: {instance.name} (workspace: {instance.workspace.name})"

    CacheInvalidationHelper.invalidate_rule_caches(rule_ids, reason)


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


# ─── DIMENSION CONSTRAINT CACHE INVALIDATION ────────────────────────────────


@receiver(post_save, sender=DimensionConstraint)
def invalidate_constraint_cache_on_save(sender, instance, created, **kwargs):
    """Invalidate constraint cache when a constraint is created or updated"""
    from ..services.constraint_validator import ConstraintValidatorService

    action = "created" if created else "updated"
    logger.info(
        f"Constraint {action}: {instance.constraint_type} for dimension {instance.dimension.name} "
        f"(order: {instance.order}, active: {instance.is_active})"
    )

    # Clear the constraint cache for this dimension
    ConstraintValidatorService.clear_constraint_cache(instance.dimension.id)


@receiver(post_delete, sender=DimensionConstraint)
def invalidate_constraint_cache_on_delete(sender, instance, **kwargs):
    """Invalidate constraint cache when a constraint is deleted"""
    from ..services.constraint_validator import ConstraintValidatorService

    logger.info(
        f"Constraint deleted: {instance.constraint_type} for dimension {instance.dimension.name}"
    )

    # Clear the constraint cache for this dimension
    ConstraintValidatorService.clear_constraint_cache(instance.dimension.id)
