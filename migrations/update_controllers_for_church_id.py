#!/usr/bin/env python3
"""
Script to update all controllers to use user.church_id instead of ChurchMembership table.

This script systematically updates all controller files that reference ChurchMembership
to use the new direct church_id field on the User model.
"""

import os
import re
import sys
from pathlib import Path

def update_file_content(file_path, replacements):
    """Update a file with the given replacements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for old_pattern, new_pattern in replacements:
            if isinstance(old_pattern, str):
                content = content.replace(old_pattern, new_pattern)
            else:  # regex pattern
                content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE | re.DOTALL)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated {file_path}")
            return True
        else:
            print(f"- No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def get_controller_files():
    """Get all controller files that need updating"""
    controller_dir = Path("app/controller")
    controller_files = []
    
    for root, dirs, files in os.walk(controller_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                # Check if file contains ChurchMembership references
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'ChurchMembership' in content:
                            controller_files.append(file_path)
                except:
                    pass
    
    return controller_files

def update_donor_management():
    """Update donor management controller"""
    file_path = "app/controller/church/donor_management.py"
    
    replacements = [
        # Remove import
        ("from app.model.m_church import ChurchMembership\n", ""),
        
        # Update join queries - pattern 1
        (re.compile(r'\.join\(\s*ChurchMembership,\s*User\.id\s*==\s*ChurchMembership\.user_id\s*\)'), ""),
        
        # Update filter conditions - pattern 1
        (re.compile(r'ChurchMembership\.church_id\s*==\s*church_id,\s*ChurchMembership\.is_active\s*==\s*True,'), 
         "User.church_id == church_id,\n            User.is_active == True,"),
        
        # Update filter conditions - pattern 2
        (re.compile(r'ChurchMembership\.church_id\s*==\s*church_id,\s*ChurchMembership\.is_active\s*==\s*True'), 
         "User.church_id == church_id,\n            User.is_active == True"),
    ]
    
    return update_file_content(file_path, replacements)

def update_church_dashboard():
    """Update church dashboard controller"""
    file_path = "app/controller/church/dashboard.py"
    
    replacements = [
        # Remove ChurchMembership import
        ("from app.model.m_church import Church, ChurchMembership", "from app.model.m_church import Church"),
        
        # Update membership count query
        (re.compile(r'db\.query\(func\.count\(ChurchMembership\.user_id\)\)\.filter\(\s*ChurchMembership\.church_id\s*==\s*church_id,\s*ChurchMembership\.is_active\s*==\s*True\s*\)'), 
         "db.query(func.count(User.id)).filter(\n            User.church_id == church_id,\n            User.is_active == True\n        )"),
        
        # Update join queries
        (re.compile(r'\.join\(ChurchMembership\)\.filter\(\s*ChurchMembership\.church_id\s*==\s*church_id,\s*ChurchMembership\.is_active\s*==\s*True,'), 
         ".filter(\n            User.church_id == church_id,\n            User.is_active == True,"),
        
        # Update other join patterns
        (re.compile(r'\.join\(Transaction\)\.join\(ChurchMembership\)\.filter\(\s*ChurchMembership\.church_id\s*==\s*church_id,\s*ChurchMembership\.is_active\s*==\s*True,'), 
         ".join(Transaction).filter(\n                User.church_id == church_id,\n                User.is_active == True,"),
    ]
    
    return update_file_content(file_path, replacements)

def update_mobile_auth():
    """Update mobile auth controller"""
    file_path = "app/controller/mobile/auth.py"
    
    replacements = [
        # Remove import if exists
        ("from app.model.m_church import ChurchMembership\n", ""),
        
        # Update any ChurchMembership queries to use user.church_id
        (re.compile(r'ChurchMembership\.user_id\s*==\s*user\.id'), "user.church_id IS NOT NULL"),
        (re.compile(r'ChurchMembership\.is_active\s*==\s*True'), "user.is_active == True"),
    ]
    
    return update_file_content(file_path, replacements)

def update_services():
    """Update service files"""
    service_files = [
        "app/services/roundup_service.py",
        "app/services/church_dashboard_service.py",
    ]
    
    updated_count = 0
    
    for file_path in service_files:
        if os.path.exists(file_path):
            replacements = [
                # Remove ChurchMembership imports
                ("from app.model.m_church import Church, ChurchMembership", "from app.model.m_church import Church"),
                (", ChurchMembership", ""),
                
                # Update queries
                (re.compile(r'db\.query\(ChurchMembership\)\.filter\(\s*ChurchMembership\.user_id\s*==\s*user_id,\s*ChurchMembership\.is_active\s*==\s*True\s*\)'), 
                 "db.query(User).filter(\n                User.id == user_id,\n                User.church_id.isnot(None),\n                User.is_active == True\n            )"),
                
                # Update membership checks
                ("membership = ", "user = "),
                ("if not membership:", "if not user or not user.church_id:"),
                ("membership.church_id", "user.church_id"),
            ]
            
            if update_file_content(file_path, replacements):
                updated_count += 1
    
    return updated_count

def update_schema_responses():
    """Update schema files to use church_id from user model"""
    file_path = "app/schema/unified_schema.py"
    
    replacements = [
        # Update the church_id assignment in user schema
        ("church_id=None,  # Note: This needs to be updated to use ChurchMembership relationship", 
         "church_id=user.church_id,"),
    ]
    
    return update_file_content(file_path, replacements)

def main():
    """Main function to update all controllers"""
    print("Starting controller updates for church_id migration...")
    
    updated_files = 0
    
    # Update specific controllers
    print("\n1. Updating donor management controller...")
    if update_donor_management():
        updated_files += 1
    
    print("\n2. Updating church dashboard controller...")
    if update_church_dashboard():
        updated_files += 1
    
    print("\n3. Updating mobile auth controller...")
    if update_mobile_auth():
        updated_files += 1
    
    print("\n4. Updating service files...")
    updated_files += update_services()
    
    print("\n5. Updating schema responses...")
    if update_schema_responses():
        updated_files += 1
    
    # Find and update any remaining controller files
    print("\n6. Scanning for remaining ChurchMembership references...")
    remaining_files = get_controller_files()
    
    if remaining_files:
        print(f"Found {len(remaining_files)} files with ChurchMembership references:")
        for file_path in remaining_files:
            print(f"  - {file_path}")
        
        # Apply generic replacements to remaining files
        generic_replacements = [
            ("from app.model.m_church import ChurchMembership\n", ""),
            (", ChurchMembership", ""),
            ("ChurchMembership", "# ChurchMembership - NEEDS MANUAL UPDATE"),
        ]
        
        for file_path in remaining_files:
            if update_file_content(file_path, generic_replacements):
                updated_files += 1
    
    print(f"\n🎉 Controller update completed!")
    print(f"Updated {updated_files} files")
    
    if remaining_files:
        print(f"\n⚠️  {len(remaining_files)} files may need manual review for ChurchMembership references")

if __name__ == "__main__":
    # Change to the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    main()
