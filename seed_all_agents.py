#!/usr/bin/env python3
"""
Seed database with all APQC agents from the generated files
"""

import os
import re
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from api_server.database import SessionLocal, Agent, engine, Base

def extract_agent_info_from_file(filepath):
    """Extract agent info from Python file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract APQC ID from filename - handle multiple patterns:
    # Pattern 1: agent_9_1_1_6_production.py -> 9.1.1.6
    # Pattern 2: 10_1_1_5_agent.py -> 10.1.1.5
    # Pattern 3: 9_1_1_agent.py -> 9.1.1 (3 parts)
    filename = os.path.basename(filepath)

    # Try pattern 1: agent_X_X_X_X
    match = re.search(r'agent_(\d+)_(\d+)_(\d+)_(\d+)', filename)
    if match:
        apqc_id = '.'.join(match.groups())
    else:
        # Try pattern 2: X_X_X_X_agent (4 parts)
        match = re.search(r'^(\d+)_(\d+)_(\d+)_(\d+)_agent', filename)
        if match:
            apqc_id = '.'.join(match.groups())
        else:
            # Try pattern 3: X_X_X_agent (3 parts)
            match = re.search(r'^(\d+)_(\d+)_(\d+)_agent', filename)
            if match:
                apqc_id = '.'.join(match.groups())
            else:
                apqc_id = None
    
    # Try to extract name and description from docstring
    name_match = re.search(r'class\s+(\w+Agent)\s*\(', content)
    name = name_match.group(1) if name_match else f"Agent {apqc_id}"
    
    doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    description = doc_match.group(1).strip() if doc_match else f"APQC Agent {apqc_id}"
    description = description[:500]  # Limit length
    
    return {
        'apqc_id': apqc_id,
        'name': name,
        'description': description
    }

def seed_all_agents():
    """Load all agents from generated files"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Find all generated agent files
        agent_patterns = [
            'generated_agents/**/*.py',
            'generated_agents_v2/**/*.py',
            'generated_production_agents/**/*.py',
            'generated_composite_agents/**/*.py'
        ]
        
        agent_files = []
        for pattern in agent_patterns:
            agent_files.extend(Path('.').glob(pattern))
        
        print(f"Found {len(agent_files)} agent files")
        
        # Check how many already exist
        existing_count = db.query(Agent).count()
        print(f"Database currently has {existing_count} agents")
        
        if existing_count > 10:
            response = input(f"Database already has {existing_count} agents. Clear and reseed? (y/n): ")
            if response.lower() == 'y':
                db.query(Agent).delete()
                db.commit()
                print("Cleared existing agents")
        
        added = 0
        skipped = 0
        
        for filepath in agent_files:
            if '__pycache__' in str(filepath) or '__init__' in str(filepath):
                continue
            
            try:
                info = extract_agent_info_from_file(filepath)
                
                if not info['apqc_id']:
                    skipped += 1
                    continue
                
                # Check if exists
                existing = db.query(Agent).filter(Agent.agent_id == f"agent_{info['apqc_id']}").first()
                if existing:
                    skipped += 1
                    continue
                
                # Add new agent
                agent = Agent(
                    agent_id=f"agent_{info['apqc_id']}",
                    name=info['name'],
                    description=info['description'],
                    apqc_id=info['apqc_id'],
                    apqc_category="APQC Process Classification Framework",
                    agent_type="atomic",
                    version="1.0.0",
                    is_active=True
                )
                
                db.add(agent)
                added += 1
                
                if added % 100 == 0:
                    print(f"  Added {added} agents...")
                    db.commit()
            
            except Exception as e:
                print(f"  Error processing {filepath}: {e}")
                continue
        
        db.commit()
        
        total = db.query(Agent).count()
        print(f"\n✅ Seeding complete!")
        print(f"   Added: {added} new agents")
        print(f"   Skipped: {skipped} agents")
        print(f"   Total in database: {total}")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_all_agents()
