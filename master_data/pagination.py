"""
Custom pagination classes for master_data API endpoints.

This module provides pagination classes with configurable limits to prevent
DoS attacks via excessive data requests.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for API endpoints.

    Features:
    - Default page size: 100 items
    - Configurable via 'page_size' query parameter
    - Maximum page size: 1000 items (hard limit to prevent DoS)

    Usage:
        GET /api/v1/endpoint/?page=2
        GET /api/v1/endpoint/?page=2&page_size=50
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

    # More descriptive query parameters
    page_query_param = 'page'

    # Custom response format
    def get_paginated_response(self, data):
        """
        Return paginated response with additional metadata.
        """
        response = super().get_paginated_response(data)

        # Add additional metadata
        response.data['page_size'] = self.page_size
        response.data['total_pages'] = self.page.paginator.num_pages

        return response
