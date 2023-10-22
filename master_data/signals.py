import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from master_data.models import Workspace, Field


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
