
"""
Service constants and configuration values.

This module contains named constants to replace magic numbers throughout the services.
Following clean code principles: constants should have clear names and documentation.
"""

# ============================================================================
# PROPAGATION THRESHOLDS
# ============================================================================

PROPAGATION_WARNING_THRESHOLD = 50
"""
Warn when string hierarchy exceeds this many children.

When a string has more than this number of direct children, a warning is
generated to alert about potentially large propagation impact.
"""

PROPAGATION_HIGH_SEVERITY_THRESHOLD = 100
"""
Mark as high severity when exceeding this threshold.

Propagations affecting more than this number of children are marked as
high severity and may require special handling or background processing.
"""

# ============================================================================
# PERFORMANCE ESTIMATES
# ============================================================================

BASE_TIME_PER_STRING_SECONDS = 0.1
"""
Estimated base processing time per string in seconds.

This is the baseline estimate for how long it takes to process a single
string regeneration, including database queries and value calculations.
"""

DEPTH_MULTIPLIER_PER_LEVEL = 0.1
"""
Additional processing time multiplier per hierarchy level.

For each level of depth in the string hierarchy, add this multiplier to
the processing time estimate. Example: depth 5 = 1 + (5 * 0.1) = 1.5x base time.
"""

# ============================================================================
# CACHE TIMEOUTS (in seconds)
# ============================================================================

CACHE_TIMEOUT_DEFAULT = 30 * 60  # 30 minutes
"""
Default cache timeout for service-level caching.

Used by RuleService, DimensionCatalogService, InheritanceMatrixService,
and FieldTemplateService for general-purpose caching.
"""

CACHE_TIMEOUT_SHORT = 5 * 60  # 5 minutes
"""
Short cache timeout for frequently changing data.

Use for data that changes often and needs fresher results.
"""

CACHE_TIMEOUT_MEDIUM = 60 * 60  # 1 hour
"""
Medium cache timeout for moderately stable data.

Use for data that changes occasionally but not frequently.
"""

CACHE_TIMEOUT_LONG = 24 * 60 * 60  # 24 hours
"""
Long cache timeout for rarely changing data.

Use for data that is very stable and rarely updated.
"""

# ============================================================================
# TIME DURATION FORMATTING
# ============================================================================

SECONDS_PER_MINUTE = 60
"""Number of seconds in one minute."""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_cache_timeout_minutes(timeout_seconds: int) -> int:
    """
    Convert cache timeout from seconds to minutes for readability.

    Args:
        timeout_seconds: Timeout value in seconds

    Returns:
        Timeout value in minutes
    """
    return timeout_seconds // SECONDS_PER_MINUTE


# ============================================================================
# CONSTANTS SUMMARY FOR QUICK REFERENCE
# ============================================================================
"""
Quick Reference:
- PROPAGATION_WARNING_THRESHOLD = 50 (warn on >50 children)
- PROPAGATION_HIGH_SEVERITY_THRESHOLD = 100 (high severity on >100 children)
- BASE_TIME_PER_STRING_SECONDS = 0.1 (base processing time)
- DEPTH_MULTIPLIER_PER_LEVEL = 0.1 (time multiplier per level)
- CACHE_TIMEOUT_DEFAULT = 1800 (30 minutes)
- CACHE_TIMEOUT_SHORT = 300 (5 minutes)
- CACHE_TIMEOUT_MEDIUM = 3600 (1 hour)
- CACHE_TIMEOUT_LONG = 86400 (24 hours)
"""
