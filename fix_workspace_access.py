#!/usr/bin/env python
"""
Quick script to grant workspace access to a user.
Run with: python manage.py shell < fix_workspace_access.py
"""

from users.models import UserAccount, WorkspaceUser
from master_data.models import Workspace, Dimension

# Get the dimension to find its workspace
dimension_id = 15
try:
    dimension = Dimension.objects.get(id=dimension_id)
    workspace = dimension.workspace
    print(f"Dimension {dimension_id} belongs to workspace: {workspace.name} (ID: {workspace.id})")

    # Get current user (adjust email as needed)
    user_email = input("Enter user email to grant access: ").strip()

    try:
        user = UserAccount.objects.get(email=user_email)
        print(f"Found user: {user.email}")

        # Check if already has access
        existing = WorkspaceUser.objects.filter(user=user, workspace=workspace).first()

        if existing:
            print(f"✅ User already has access to workspace as {existing.role}")
        else:
            # Grant access
            WorkspaceUser.objects.create(
                user=user,
                workspace=workspace,
                role='admin'
            )
            print(f"✅ Granted admin access to {workspace.name} for {user.email}")

    except UserAccount.DoesNotExist:
        print(f"❌ User with email {user_email} not found")
        print("\nAvailable users:")
        for u in UserAccount.objects.all()[:10]:
            print(f"  - {u.email}")

except Dimension.DoesNotExist:
    print(f"❌ Dimension with ID {dimension_id} not found")
    print("\nAvailable dimensions:")
    for d in Dimension.objects.all()[:10]:
        print(f"  - ID {d.id}: {d.name} (Workspace: {d.workspace.name})")
