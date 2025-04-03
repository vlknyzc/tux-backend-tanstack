from django.db import models


def default_workspace_logo():
    return "workspaces/default/default-workspace-logo.png"


class TimeStampModel(models.Model):
    """Base model that includes created and last_updated timestamps."""
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
