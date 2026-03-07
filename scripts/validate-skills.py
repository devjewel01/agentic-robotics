#!/usr/bin/env python3
"""
Validate SKILL.md files for format compliance.
Usage: python scripts/validate-skills.py skills/skill-name/
"""

import sys
import re
import os
from pathlib import Path


def validate_frontmatter(content):
    """Validate YAML frontmatter."""
    errors = []
    
    # Check for frontmatter delimiters
    if not content.startswith('---'):
        errors.append("Missing opening '---' for YAML frontmatter")
        return errors
    
    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not match:
        errors.append("Invalid frontmatter format")
        return errors
    
    frontmatter = match.group(1)
    
    # Required fields
    required_fields = ['name:', 'description:', 'category:']
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")
    
    # Check category is valid
    valid_categories = [
        'middleware', 'simulation', 'perception', 'navigation',
        'manipulation', 'control', 'hardware', 'embedded', 'ai',
        'architecture', 'devops'
    ]
    category_match = re.search(r'category:\s*(\w+)', frontmatter)
    if category_match:
        category = category_match.group(1)
        if category not in valid_categories:
            errors.append(f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}")
    
    return errors


def validate_sections(content):
    """Validate required sections."""
    errors = []
    
    required_sections = [
        '## When to Use',
        '## Quick Start',
        '## Core Concepts',
        '## Common Patterns',
        '## Anti-Patterns',
        '## Configuration Reference',
        '## Troubleshooting',
        '## Workflow Integration'
    ]
    
    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section: {section}")
    
    return errors


def validate_size(content):
    """Validate skill size."""
    errors = []
    lines = content.split('\n')
    line_count = len(lines)
    
    if line_count < 500:
        errors.append(f"Skill too short ({line_count} lines). Minimum 500 lines.")
    elif line_count > 3000:
        errors.append(f"Skill too long ({line_count} lines). Maximum 3000 lines.")
    
    return errors, line_count


def validate_skill(skill_path):
    """Validate a single skill."""
    skill_path = Path(skill_path)
    
    if not skill_path.exists():
        print(f"❌ Error: Path does not exist: {skill_path}")
        return False
    
    # Find SKILL.md
    if skill_path.is_dir():
        skill_file = skill_path / 'SKILL.md'
    else:
        skill_file = skill_path
    
    if not skill_file.exists():
        print(f"❌ Error: SKILL.md not found in {skill_path}")
        return False
    
    # Read content
    content = skill_file.read_text()
    
    # Run validations
    all_errors = []
    
    frontmatter_errors = validate_frontmatter(content)
    all_errors.extend(frontmatter_errors)
    
    section_errors = validate_sections(content)
    all_errors.extend(section_errors)
    
    size_errors, line_count = validate_size(content)
    all_errors.extend(size_errors)
    
    # Report results
    skill_name = skill_path.name if skill_path.is_dir() else skill_path.stem
    
    if all_errors:
        print(f"\n❌ {skill_name}")
        for error in all_errors:
            print(f"   - {error}")
        return False
    else:
        print(f"✅ {skill_name} ({line_count} lines)")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate-skills.py <skill-path> [skill-path...]")
        print("       python scripts/validate-skills.py --all")
        sys.exit(1)
    
    if sys.argv[1] == '--all':
        # Validate all skills
        skills_dir = Path('skills')
        if not skills_dir.exists():
            print("❌ Error: skills/ directory not found")
            sys.exit(1)
        
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        if not skill_dirs:
            print("No skills found in skills/")
            sys.exit(0)
        
        print(f"Validating {len(skill_dirs)} skills...\n")
        
        passed = 0
        failed = 0
        
        for skill_dir in sorted(skill_dirs):
            if validate_skill(skill_dir):
                passed += 1
            else:
                failed += 1
        
        print(f"\n{'='*50}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            sys.exit(1)
    else:
        # Validate specific skills
        passed = 0
        failed = 0
        
        for skill_path in sys.argv[1:]:
            if validate_skill(skill_path):
                passed += 1
            else:
                failed += 1
        
        if failed > 0:
            sys.exit(1)


if __name__ == '__main__':
    main()