"""
Signal handlers for master_data app.
"""

# Import signal handlers to ensure they are registered
from .string_propagation import (
    capture_stringdetail_pre_save_state,
    enhanced_auto_regenerate_string_on_detail_update
)