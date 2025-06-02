# Related Name Fix Documentation

## 🚨 **Issue Encountered**

**Error Message:**

```
AttributeError at /api/nested-submissions/
Cannot find 'strings' on Submission object, 'strings' is an invalid parameter to prefetch_related()
```

**Root Cause:**
During our related name conflict fixes (migration `0006_fix_related_name_conflicts.py`), we changed the related name for the `String.submission` field from `strings` to `submission_strings` to resolve conflicts. However, some code in the nested submission views and serializers was still using the old `strings` related name.

---

## 🔧 **Files Fixed**

### **1. Nested Submission Views**

**File:** `master_data/views/nested_submission_views.py`

**Before:**

```python
.prefetch_related(
    'strings',
    'strings__field',
    'strings__string_details',
    'strings__string_details__dimension',
    'strings__string_details__dimension_value'
)
```

**After:**

```python
.prefetch_related(
    'submission_strings',
    'submission_strings__field',
    'submission_strings__string_details',
    'submission_strings__string_details__dimension',
    'submission_strings__string_details__dimension_value'
)
```

### **2. Nested Submission Serializer**

**File:** `master_data/serializers/nested_submission.py`

**Before:**

```python
class SubmissionNestedSerializer(serializers.ModelSerializer):
    blocks = StringNestedSerializer(
        source='strings', many=True, required=False)

    def create(self, validated_data):
        blocks_data = validated_data.pop('strings', [])

    def update(self, instance, validated_data):
        blocks_data = validated_data.pop('strings', [])
        instance.strings.all().delete()
```

**After:**

```python
class SubmissionNestedSerializer(serializers.ModelSerializer):
    blocks = StringNestedSerializer(
        source='submission_strings', many=True, required=False)

    def create(self, validated_data):
        blocks_data = validated_data.pop('submission_strings', [])

    def update(self, instance, validated_data):
        blocks_data = validated_data.pop('submission_strings', [])
        instance.submission_strings.all().delete()
```

---

## ✅ **Related Name Reference**

For future reference, here are the correct related names after the conflict fixes:

### **String Model Relationships**

```python
# String model (master_data/models/string.py)
class String(TimeStampModel):
    submission = models.ForeignKey(
        "master_data.Submission",
        related_name="submission_strings",  # ✅ Correct
        # ...
    )

    field = models.ForeignKey(
        "master_data.Field",
        related_name="field_strings",  # ✅ Correct
        # ...
    )

    parent = models.ForeignKey(
        "master_data.String",
        related_name="child_strings",  # ✅ Correct
        # ...
    )
```

### **Usage Examples**

```python
# ✅ Correct usage in queries
submission.submission_strings.all()  # Get all strings for a submission
field.field_strings.all()           # Get all strings for a field
string.child_strings.all()          # Get child strings

# ✅ Correct usage in prefetch_related
queryset.prefetch_related('submission_strings')
queryset.prefetch_related('submission_strings__field')
queryset.prefetch_related('submission_strings__string_details')

# ✅ Correct usage in serializers
class MySerializer(serializers.ModelSerializer):
    strings = StringSerializer(source='submission_strings', many=True)
```

---

## 🧪 **Validation**

### **System Checks**

- ✅ `python manage.py check` - No issues identified
- ✅ All 78 URL patterns registered successfully
- ✅ API endpoint tests pass without errors

### **Endpoints Tested**

- ✅ `/api/nested-submissions/` - Now works correctly
- ✅ All string generation endpoints functional
- ✅ All rule management endpoints functional

---

## 📚 **Related Name Best Practices**

### **1. Naming Convention**

Use descriptive related names that clearly indicate the relationship:

```python
# ❌ Ambiguous
related_name="strings"

# ✅ Clear and descriptive
related_name="submission_strings"
related_name="field_strings"
related_name="child_strings"
```

### **2. Avoid Conflicts**

When multiple models have relationships to the same model, ensure unique related names:

```python
# Models that both relate to String
class Submission(models.Model):
    # strings = related_name for submission strings
    pass

class Field(models.Model):
    # strings = related_name for field strings - CONFLICT!
    pass

# Solution: Use specific related names
submission = models.ForeignKey(related_name="submission_strings")
field = models.ForeignKey(related_name="field_strings")
```

### **3. Consistency Checks**

When updating related names:

1. **Check views** for `prefetch_related()` usage
2. **Check serializers** for `source=` parameters
3. **Check templates** for relationship access
4. **Run system checks** to validate
5. **Test API endpoints** to ensure functionality

---

## 🎯 **Key Takeaway**

When fixing related name conflicts, it's crucial to update **all references** throughout the codebase:

- Model field definitions ✅
- View querysets ✅
- Serializer sources ✅
- Template references
- Any direct relationship access

The error was resolved by updating the remaining references to use the new `submission_strings` related name consistently across the views and serializers! 🚀
