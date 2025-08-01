#!/usr/bin/env python
"""
Test script to verify string regeneration is working.
Run with: python manage.py shell < test_regeneration.py
"""

from master_data.models import StringDetail, DimensionValue

# Test the regeneration
detail = StringDetail.objects.get(id=137)
cat3_value = DimensionValue.objects.get(value='cat-3')

print(f"Before: StringDetail={detail.dimension_value.value}, String={detail.string.value}")

# Update and save
detail.dimension_value = cat3_value  
detail.save()

print(f"After: StringDetail={detail.dimension_value.value}, String={detail.string.value}")

# The string should now show "eu_us_cat-3"