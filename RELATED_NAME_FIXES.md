# Related Name Conflicts - Fixed

## Overview

Fixed all related name conflicts across the master_data models to improve code clarity and prevent Django relationship conflicts.

## Changes Made

### 1. Submission Model (`submission.py`)

**Before:** `rule = ForeignKey(..., related_name="strings")`
**After:** `rule = ForeignKey(..., related_name="submissions")`
**Reason:** The related name should describe what's being related - submissions, not strings.

### 2. Field Model (`field.py`)

**Before:** `next_field = ForeignKey(..., related_name="fields")`
**After:** `next_field = ForeignKey(..., related_name="child_fields")`
**Reason:** Conflicted with `platform.fields` relationship. Now it's clear this refers to child fields in a hierarchy.

### 3. String Model (`string.py`)

**Before:**

- `parent = ForeignKey(..., related_name="strings")`
- `field = ForeignKey(..., related_name="strings")`
- `submission = ForeignKey(..., related_name="strings")`

**After:**

- `parent = ForeignKey(..., related_name="child_strings")`
- `field = ForeignKey(..., related_name="field_strings")`
- `submission = ForeignKey(..., related_name="submission_strings")`

**Reason:** All three relationships used the same related_name causing conflicts. Now each is specific and descriptive.

### 4. Dimension Models (`dimension.py`)

**Before:**

- `parent = ForeignKey(..., related_name="dimensions")` (Dimension)
- `parent = ForeignKey(..., related_name="dimension_values")` (DimensionValue)

**After:**

- `parent = ForeignKey(..., related_name="child_dimensions")` (Dimension)
- `parent = ForeignKey(..., related_name="child_dimension_values")` (DimensionValue)

**Reason:** The DimensionValue parent relationship conflicted with `dimension.dimension_values`.

## Benefits

### ✅ **Clarity**

- Related names now clearly indicate the relationship direction and purpose
- No more ambiguous `strings` or `fields` related names

### ✅ **No Conflicts**

- Each related name is unique across the entire app
- Django can properly generate reverse relationships

### ✅ **Better API**

- Developers can easily understand what each relationship returns:
  - `rule.submissions` - all submissions for this rule
  - `field.child_fields` - fields that come after this field
  - `dimension.child_dimensions` - sub-dimensions
  - `string.child_strings` - strings that have this as parent

## Migration Applied

- Created migration: `0006_fix_related_name_conflicts.py`
- Successfully applied without issues
- All Django checks pass

## Usage Examples

```python
# Before (confusing/conflicting):
rule.strings  # Was this submissions or actual strings?
field.fields  # Conflicted with platform.fields

# After (clear and specific):
rule.submissions          # Clear: submissions using this rule
rule.rule_strings        # Clear: actual string records for this rule
field.child_fields       # Clear: fields that follow this field
platform.fields          # Clear: fields belonging to platform
dimension.child_dimensions  # Clear: sub-dimensions
```

## Next Steps

This resolves the high-priority related name conflicts. Ready to move on to the next improvement category.
