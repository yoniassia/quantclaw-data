#!/usr/bin/env python3
"""
API Key Environment Variable Migration Script

Scans all Python modules and replaces hardcoded API keys with os.environ.get() calls.
Creates backups before modifying files.
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load .env to verify keys exist
load_dotenv('/home/quant/apps/quantclaw-data/.env')

# API keys to migrate
API_KEYS = [
    'FRED_API_KEY',
    'EIA_API_KEY', 
    'CENSUS_API_KEY',
    'FINNHUB_API_KEY',
    'ETHERSCAN_API_KEY',
    'POLYGON_API_KEY',
    'USDA_NASS_API_KEY',
    'NASS_API_KEY',
    'BLS_API_KEY',
    'BOK_API_KEY',
    'COMTRADE_API_KEY',
    'IEX_API_KEY',
    'CRUNCHBASE_API_KEY',
    'SPACINSIDER_API_KEY',
    'DEFAULT_API_KEY',
    'API_KEY',  # Generic pattern
]

# Directories to scan
MODULES_DIR = Path('/home/quant/apps/quantclaw-data/modules')
BACKUP_DIR = Path('/home/quant/apps/quantclaw-data/backups_api_migration')
LOG_FILE = Path('/home/quant/apps/quantclaw-data/api_migration.log')

class APIKeyPatcher:
    def __init__(self):
        self.changes_log = []
        self.files_modified = 0
        self.backup_dir = BACKUP_DIR / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str):
        """Log message to console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        self.changes_log.append(log_msg)
        
    def backup_file(self, file_path: Path) -> Path:
        """Create backup of file before modification"""
        backup_path = self.backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        return backup_path
        
    def has_api_key_pattern(self, content: str) -> bool:
        """Check if file contains API key patterns"""
        for key in API_KEYS:
            # Match various patterns:
            # KEY = "value" or KEY = '' or KEY = None or self.key = "value"
            patterns = [
                rf'{key}\s*=\s*["\'][^"\']*["\']',
                rf'{key}\s*=\s*None',
                rf'{key}\s*=\s*""',
                rf'{key}\s*=\s*\'\'',
                rf'self\.{key.lower()}\s*=\s*["\'][^"\']*["\']',
            ]
            for pattern in patterns:
                if re.search(pattern, content):
                    return True
        return False
        
    def needs_imports(self, content: str) -> Tuple[bool, bool, bool]:
        """Check which imports are needed"""
        needs_os = 'import os' not in content
        needs_dotenv_import = 'from dotenv import load_dotenv' not in content
        needs_dotenv_call = 'load_dotenv()' not in content
        return needs_os, needs_dotenv_import, needs_dotenv_call
        
    def add_imports(self, content: str) -> str:
        """Add necessary imports at the top of file"""
        needs_os, needs_dotenv_import, needs_dotenv_call = self.needs_imports(content)
        
        lines = content.split('\n')
        
        # Find the insertion point (after shebang and docstrings)
        insert_idx = 0
        in_docstring = False
        docstring_char = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip shebang
            if i == 0 and stripped.startswith('#!'):
                insert_idx = i + 1
                continue
                
            # Track docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    docstring_char = stripped[:3]
                elif stripped.endswith(docstring_char):
                    in_docstring = False
                    insert_idx = i + 1
                continue
                
            if in_docstring:
                continue
                
            # Stop at first import or code
            if stripped and not stripped.startswith('#'):
                if not stripped.startswith('import') and not stripped.startswith('from'):
                    insert_idx = i
                break
                
        # Build import block
        imports_to_add = []
        if needs_os:
            imports_to_add.append('import os')
        if needs_dotenv_import:
            imports_to_add.append('from dotenv import load_dotenv')
            
        if imports_to_add:
            # Insert imports
            for imp in reversed(imports_to_add):
                lines.insert(insert_idx, imp)
            
            # Add load_dotenv() call after imports if needed
            if needs_dotenv_call and needs_dotenv_import:
                # Find where to add load_dotenv() - after all imports
                for i in range(insert_idx, len(lines)):
                    stripped = lines[i].strip()
                    if stripped and not stripped.startswith('import') and not stripped.startswith('from') and not stripped.startswith('#'):
                        lines.insert(i, '\n# Load environment variables')
                        lines.insert(i + 1, 'load_dotenv()')
                        lines.insert(i + 2, '')
                        break
                        
        return '\n'.join(lines)
        
    def replace_api_keys(self, content: str, filename: str) -> Tuple[str, List[str]]:
        """Replace hardcoded API keys with os.environ.get() calls"""
        changes = []
        modified_content = content
        
        for key in API_KEYS:
            # Pattern 1: Direct assignment KEY = "value" or KEY = '' or KEY = None
            patterns_and_replacements = [
                # Match: KEY = "anything" or KEY = 'anything'
                (rf'({key})\s*=\s*["\'][^"\']*["\']', 
                 rf'\1 = os.environ.get("{key}", "")'),
                # Match: KEY = None
                (rf'({key})\s*=\s*None', 
                 rf'\1 = os.environ.get("{key}", "")'),
                # Match: self.key = "value" (convert key to uppercase for env var)
                (rf'(self\.{key.lower()})\s*=\s*["\'][^"\']*["\']',
                 rf'\1 = os.environ.get("{key}", "")'),
            ]
            
            for pattern, replacement in patterns_and_replacements:
                matches = list(re.finditer(pattern, modified_content))
                if matches:
                    for match in matches:
                        original = match.group(0)
                        new_value = re.sub(pattern, replacement, original)
                        changes.append(f"  {original} → {new_value}")
                    modified_content = re.sub(pattern, replacement, modified_content)
                    
        return modified_content, changes
        
    def patch_file(self, file_path: Path) -> bool:
        """Patch a single file"""
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Skip if no API key patterns
            if not self.has_api_key_pattern(original_content):
                return False
                
            # Create backup
            backup_path = self.backup_file(file_path)
            self.log(f"\n📁 Processing: {file_path.name}")
            self.log(f"   Backup: {backup_path}")
            
            # Add imports
            content_with_imports = self.add_imports(original_content)
            
            # Replace API keys
            modified_content, changes = self.replace_api_keys(content_with_imports, file_path.name)
            
            if changes:
                self.log(f"   Changes made:")
                for change in changes:
                    self.log(change)
                    
                # Write modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                    
                self.files_modified += 1
                return True
            else:
                self.log(f"   No changes needed (imports only added)")
                # Still write the file if imports were added
                if content_with_imports != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content_with_imports)
                    self.files_modified += 1
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error processing {file_path.name}: {str(e)}")
            return False
            
    def patch_all_modules(self):
        """Patch all Python files in modules directory"""
        self.log("=" * 80)
        self.log("API Key Environment Variable Migration")
        self.log("=" * 80)
        self.log(f"Scanning directory: {MODULES_DIR}")
        self.log(f"Backup directory: {self.backup_dir}")
        self.log("")
        
        # Find all Python files
        py_files = list(MODULES_DIR.glob('*.py'))
        self.log(f"Found {len(py_files)} Python files")
        
        files_with_changes = 0
        for py_file in sorted(py_files):
            if self.patch_file(py_file):
                files_with_changes += 1
                
        # Write log file
        with open(LOG_FILE, 'w') as f:
            f.write('\n'.join(self.changes_log))
            
        self.log("")
        self.log("=" * 80)
        self.log("SUMMARY")
        self.log("=" * 80)
        self.log(f"Total files scanned: {len(py_files)}")
        self.log(f"Files modified: {self.files_modified}")
        self.log(f"Files with API key changes: {files_with_changes}")
        self.log(f"Backup location: {self.backup_dir}")
        self.log(f"Log file: {LOG_FILE}")
        self.log("=" * 80)

def main():
    patcher = APIKeyPatcher()
    patcher.patch_all_modules()
    
if __name__ == '__main__':
    main()
