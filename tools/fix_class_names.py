#!/usr/bin/env python3
"""
Fix Invalid Class Names

Fixes Python class names that contain invalid characters like commas and hyphens.
These were generated from APQC process names that contain special characters.

Usage:
    python tools/fix_class_names.py --scan           # List files with issues
    python tools/fix_class_names.py --fix            # Fix all issues
    python tools/fix_class_names.py --file <path>    # Fix specific file
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Dict


def fix_class_name(name: str) -> str:
    """
    Fix a class name by removing invalid characters and applying PascalCase.

    Examples:
        "DevelopManageHrPlanning,Policies,Strategies" -> "DevelopManageHrPlanningPoliciesStrategies"
        "DefineBusinessConceptLong-termVision" -> "DefineBusinessConceptLongTermVision"
        "DevelopManageEnterprise-wideKnowledge" -> "DevelopManageEnterpriseWideKnowledge"
    """
    result = []
    capitalize_next = False

    for i, char in enumerate(name):
        if char == ',':
            # Skip comma, capitalize next letter
            capitalize_next = True
        elif char == '-':
            # Skip hyphen, capitalize next letter
            capitalize_next = True
        else:
            if capitalize_next and char.isalpha():
                result.append(char.upper())
                capitalize_next = False
            else:
                result.append(char)

    return ''.join(result)


def find_invalid_class_names(content: str) -> List[Tuple[str, str]]:
    """
    Find class names with invalid characters and their fixed versions.
    Returns list of (original, fixed) tuples.
    """
    replacements = []

    # Pattern to find class declarations with invalid characters
    class_pattern = r'class\s+([A-Za-z0-9_,\-]+(?:Config|Agent))\s*[:\(]'
    for match in re.finditer(class_pattern, content):
        original = match.group(1)
        if ',' in original or '-' in original:
            fixed = fix_class_name(original)
            if original != fixed:
                replacements.append((original, fixed))

    # Pattern to find function names with invalid characters (create_*_agent functions)
    func_pattern = r'def\s+(create_[a-z0-9_,\-]+_agent)\s*\('
    for match in re.finditer(func_pattern, content):
        original = match.group(1)
        if ',' in original or '-' in original:
            fixed = fix_function_name(original)
            if original != fixed:
                replacements.append((original, fixed))

    return replacements


def fix_function_name(name: str) -> str:
    """
    Fix a function name by removing invalid characters.
    Function names use snake_case, so we just remove commas and hyphens.

    Examples:
        "create_develop_manage_hr_planning,_policies,_strategies_human_capital_agent"
        -> "create_develop_manage_hr_planning_policies_strategies_human_capital_agent"
    """
    # Remove commas (and the following underscore if present)
    name = re.sub(r',_?', '_', name)
    # Replace hyphens with underscores
    name = name.replace('-', '_')
    # Remove double underscores
    name = re.sub(r'_+', '_', name)
    return name


def fix_file(file_path: str, dry_run: bool = False) -> Tuple[bool, str, List[Tuple[str, str]]]:
    """
    Fix invalid class names in a file.
    Returns (success, message, replacements made).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        replacements = find_invalid_class_names(content)

        if not replacements:
            return True, "No invalid class names found", []

        # Apply all replacements
        for original, fixed in replacements:
            # Check if it's a function name (starts with create_) or class name
            if original.startswith('create_'):
                # Function name replacement
                content = content.replace(f'def {original}(', f'def {fixed}(')
                content = content.replace(f' {original}(', f' {fixed}(')
                content = content.replace(f'"{original}"', f'"{fixed}"')
                content = content.replace(f"'{original}'", f"'{fixed}'")
            else:
                # Class name replacement
                content = content.replace(f'class {original}:', f'class {fixed}:')
                content = content.replace(f'class {original}(', f'class {fixed}(')

                # Replace type hints and references
                content = content.replace(f'"{original}"', f'"{fixed}"')
                content = content.replace(f"'{original}'", f"'{fixed}'")
                content = content.replace(f' {original}(', f' {fixed}(')
                content = content.replace(f' {original}.', f' {fixed}.')
                content = content.replace(f'({original})', f'({fixed})')
                content = content.replace(f'[{original}]', f'[{fixed}]')
                content = content.replace(f'->{original}', f'->{fixed}')
                content = content.replace(f'-> {original}', f'-> {fixed}')
                content = content.replace(f': {original}', f': {fixed}')
                content = content.replace(f':{original}', f':{fixed}')

        if content == original_content:
            return True, "No changes needed", []

        if dry_run:
            return True, f"Would fix {len(replacements)} class names", replacements

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, f"Fixed {len(replacements)} class names", replacements

    except Exception as e:
        return False, f"Error: {e}", []


def scan_directory(directory: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """
    Scan directory for files with invalid class names.
    Returns list of (file_path, [(original, fixed), ...]).
    """
    issues = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    replacements = find_invalid_class_names(content)
                    if replacements:
                        issues.append((file_path, replacements))
                except Exception:
                    pass

    return issues


def main():
    parser = argparse.ArgumentParser(description='Fix invalid Python class names')
    parser.add_argument('--scan', action='store_true', help='Scan for files with issues')
    parser.add_argument('--fix', action='store_true', help='Fix all issues')
    parser.add_argument('--file', type=str, help='Fix specific file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent / 'src' / 'superstandard' / 'agents'

    if args.scan:
        print(f"\nScanning {base_dir} for invalid class names...\n")
        issues = scan_directory(str(base_dir))

        if not issues:
            print("No issues found!")
            return

        print(f"Found {len(issues)} files with invalid class names:\n")
        for file_path, replacements in issues:
            print(f"\n{file_path}:")
            for original, fixed in replacements:
                print(f"  {original} -> {fixed}")

        print(f"\nTotal: {len(issues)} files need fixing")
        print("Run with --fix to apply fixes")
        return

    if args.file:
        success, message, replacements = fix_file(args.file, dry_run=args.dry_run)
        print(f"{'[DRY-RUN] ' if args.dry_run else ''}{message}")
        for original, fixed in replacements:
            print(f"  {original} -> {fixed}")
        return

    if args.fix:
        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Fixing invalid class names in {base_dir}...\n")
        issues = scan_directory(str(base_dir))

        if not issues:
            print("No issues found!")
            return

        fixed_count = 0
        error_count = 0

        for file_path, _ in issues:
            success, message, replacements = fix_file(file_path, dry_run=args.dry_run)
            status = "[OK]" if success else "[FAIL]"
            print(f"{status} {file_path}: {message}")

            if success and replacements:
                fixed_count += 1
            elif not success:
                error_count += 1

        print(f"\n{'Dry run complete' if args.dry_run else 'Complete'}: {fixed_count} files fixed, {error_count} errors")
        return

    parser.print_help()


if __name__ == '__main__':
    main()
