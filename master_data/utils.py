"""
Utility functions for the master_data app.
"""

from django.utils.text import slugify


def generate_unique_slug(instance, source_field_name, slug_field_name='slug', max_length=50):
    """
    Generate a unique slug for a model instance, scoped by workspace if applicable.
    """
    Model = instance.__class__
    source_value = getattr(instance, source_field_name)

    if not source_value:
        return ''

    # Generate base slug
    base_slug = slugify(source_value)[:max_length]
    slug = base_slug

    # Check for uniqueness and append counter if needed
    counter = 1
    while True:
        # Build the queryset to check for conflicts
        qs = Model.objects.filter(**{slug_field_name: slug})

        # Exclude current instance if it's being updated
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)

        # If the model has a workspace field, scope by workspace
        if hasattr(instance, 'workspace_id') and instance.workspace_id:
            qs = qs.filter(workspace_id=instance.workspace_id)

        # If no conflicts, we have a unique slug
        if not qs.exists():
            break

        # Generate new slug with counter
        counter_suffix = f'-{counter}'
        max_base_length = max_length - len(counter_suffix)
        slug = f'{base_slug[:max_base_length]}{counter_suffix}'
        counter += 1

    return slug



