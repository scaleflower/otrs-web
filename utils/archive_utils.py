"""
Common utilities for archive file validation and extraction.

This module provides shared functionality for validating archive members
to prevent path traversal attacks and other security issues.
"""

from __future__ import annotations

import os
import tarfile
from pathlib import Path
from typing import Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import zipfile


class ArchiveValidationError(Exception):
    """Raised when archive member validation fails."""


def validate_members(
    members: Iterable,
    dest_dir: Path,
    zip_mode: bool = False,
) -> List:
    """
    Validate archive members to prevent path traversal or unsafe entries.
    
    Args:
        members: Archive members to validate
        dest_dir: Destination directory for extraction
        zip_mode: Whether processing a ZIP archive
        
    Returns:
        List of safe members
        
    Raises:
        ArchiveValidationError: If unsafe members are detected
    """
    dest_root = dest_dir.resolve()
    safe_members = []
    
    for member in members:
        name = member.filename if zip_mode else member.name
        if not name:
            raise ArchiveValidationError("Encountered archive member with empty name")
            
        # Normalize path separators
        normalized_name = name.replace("\\", "/")
        # Remove leading ./ segments
        while normalized_name.startswith("./"):
            normalized_name = normalized_name[2:]
            
        # Check for absolute paths or parent directory traversal
        if (
            normalized_name.startswith("/") 
            or normalized_name.startswith("../") 
            or "/../" in normalized_name
        ):
            raise ArchiveValidationError(f"Blocked unsafe absolute or parent path: {name}")
            
        # Resolve the target path and ensure it's within the destination
        member_path = dest_root / normalized_name
        try:
            resolved = member_path.resolve()
        except FileNotFoundError:
            # Parent directories may not exist yet; resolve parent
            resolved = member_path.parent.resolve()
            
        if not str(resolved).startswith(str(dest_root)):
            raise ArchiveValidationError(f"Blocked unsafe path traversal for member: {name}")
            
        # Additional checks for tar members
        if not zip_mode:
            # Block symbolic links and hard links which can be used maliciously
            if getattr(member, "issym", lambda: False)() or getattr(member, "islnk", lambda: False)():
                raise ArchiveValidationError(f"Blocked archive member with link type: {name}")
                
        safe_members.append(member)
        
    return safe_members