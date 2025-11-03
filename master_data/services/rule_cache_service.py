"""
RuleCacheService: Manages caching for rule operations.

This service handles cache invalidation and management for rule-related data,
coordinating between multiple service caches (dimension catalog, inheritance matrix,
field templates) and Django's cache framework.

Part of the refactoring from God Class (Issue #13) to separate cache concerns
from business logic.
"""

from typing import List, Optional, Any
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class RuleCacheService:
    """
    Service for managing rule-related caches.

    Responsibilities:
    - Cache invalidation for individual rules
    - Bulk cache invalidation for multiple rules
    - Rule configuration cache management
    - Coordination between service-level caches

    This service acts as a central point for cache management,
    ensuring consistency across all rule-related cached data.
    """

    def __init__(self):
        """Initialize cache service."""
        self.cache_timeout = 30 * 60  # 30 minutes default

    def invalidate_all_caches(self, rule):
        """
        Invalidate all caches for a rule across all services.

        This method coordinates cache invalidation across:
        - Dimension catalog caches
        - Inheritance matrix caches
        - Field template caches
        - Complete rule data caches
        - Django page caches

        Args:
            rule: Rule instance or rule ID

        Note:
            This method requires coordination with the service layer.
            In the facade pattern, the RuleService will handle this coordination.
        """
        # Import here to avoid circular imports
        from .dimension_catalog_service import DimensionCatalogService
        from .inheritance_matrix_service import InheritanceMatrixService
        from .field_template_service import FieldTemplateService

        # Get rule ID
        rule_id = rule.id if hasattr(rule, 'id') else rule

        # Invalidate individual service caches
        dimension_service = DimensionCatalogService()
        inheritance_service = InheritanceMatrixService()
        template_service = FieldTemplateService()

        dimension_service.invalidate_cache(rule_id)
        inheritance_service.invalidate_cache(rule_id)
        template_service.invalidate_cache(rule_id)

        # Invalidate complete data cache
        cache_key = f"complete_rule_data:{rule_id}"
        cache.delete(cache_key)

        # Clear Django's page cache for rule configuration endpoint
        cache_key = f"views.decorators.cache.cache_page.{rule_id}.GET"
        cache.delete(cache_key)

        logger.info(f"Invalidated all caches for rule {rule_id}")

    def bulk_invalidate_caches(self, rules: List):
        """
        Invalidate caches for multiple rules.

        Args:
            rules: List of Rule instances or rule IDs
        """
        for rule in rules:
            self.invalidate_all_caches(rule)

        rule_ids = [r.id if hasattr(r, 'id') else r for r in rules]
        logger.info(f"Bulk invalidated caches for {len(rules)} rules: {rule_ids}")

    def clear_rule_configuration_cache(self, rule_id: int):
        """
        Clear cache specifically for rule configuration endpoint.

        This method uses the centralized cache invalidation helper
        to ensure consistent cache clearing across the application.

        Args:
            rule_id: ID of the rule
        """
        from ..signals.cache_invalidation import CacheInvalidationHelper

        # Use the centralized cache invalidation helper
        CacheInvalidationHelper.invalidate_rule_caches(
            [rule_id],
            "Manual cache clear"
        )

        logger.info(f"Cleared rule configuration cache for rule {rule_id}")

    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if not found
        """
        return cache.get(cache_key)

    def set_cached_data(self, cache_key: str, value: Any, timeout: Optional[int] = None):
        """
        Set data in cache.

        Args:
            cache_key: Cache key
            value: Data to cache
            timeout: Cache timeout in seconds (default: 30 minutes)
        """
        timeout = timeout or self.cache_timeout
        cache.set(cache_key, value, timeout)
        logger.debug(f"Set cache for key {cache_key} with timeout {timeout}s")

    def delete_cache_key(self, cache_key: str):
        """
        Delete specific cache key.

        Args:
            cache_key: Cache key to delete
        """
        cache.delete(cache_key)
        logger.debug(f"Deleted cache key: {cache_key}")

    def delete_cache_keys(self, cache_keys: List[str]):
        """
        Delete multiple cache keys.

        Args:
            cache_keys: List of cache keys to delete
        """
        cache.delete_many(cache_keys)
        logger.debug(f"Deleted {len(cache_keys)} cache keys")
