#!/usr/bin/env python3
"""
Collect training data from JEBAT codebase.
Creates instruction/response pairs for fine-tuning.
"""

import json
import re
from pathlib import Path
from typing import List, Dict

def collect_code_examples(root_dir: str) -> List[Dict]:
    """Collect code examples from Python files."""
    examples = []
    root = Path(root_dir)
    
    for py_file in root.rglob("*.py"):
        if ".git" in str(py_file) or "node_modules" in str(py_file):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            rel_path = py_file.relative_to(root)
            
            # Extract docstring if exists
            docstring = ""
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if '"""' in line or "'''" in line:
                    doc_start = i
                    for j in range(i+1, min(i+10, len(lines))):
                        if '"""' in lines[j] or "'''" in lines[j]:
                            docstring = "\n".join(lines[doc_start:j+1])
                            break
                    break
            
            example = {
                "instruction": f"Explain and analyze this Python code from {rel_path}",
                "input": docstring if docstring else f"Code from {rel_path}",
                "output": f"```python\n{content[:2000]}\n```"
            }
            examples.append(example)
            
        except Exception as e:
            continue
    
    return examples

def collect_system_prompts(root_dir: str) -> List[Dict]:
    """Collect system prompts and configurations."""
    examples = []
    root = Path(root_dir)
    
    for md_file in ["AGENTS.md", "CLAUDE.md", "DESIGN.md", "MEMORY.md"]:
        file_path = root / md_file
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            example = {
                "instruction": f"Explain the {md_file} configuration for JEBAT",
                "input": f"This is the {md_file} file content",
                "output": content[:2000]
            }
            examples.append(example)
    
    return examples

def collect_cli_commands(root_dir: str) -> List[Dict]:
    """Collect CLI command definitions."""
    examples = []
    
    jebat_py = Path(root_dir) / "jebat-core" / "jebat_cli_new" / "jebat.py"
    if jebat_py.exists():
        with open(jebat_py, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple pattern to find command strings
        pattern = r'"(/[a-z-]+)"\s*,\s*"([^"]+)"'
        matches = re.findall(pattern, content)
        
        for cmd, desc in matches[:50]:  # Limit to first 50
            example = {
                "instruction": f"How do I use the {cmd} command in JEBAT CLI?",
                "input": desc,
                "output": f"To use {cmd}: {desc}. Run it with: jebat {cmd}"
            }
            examples.append(example)
    
    return examples

def create_training_dataset(root_dir: str, output_file: str):
    """Create the complete training dataset."""
    print("Collecting code examples...")
    code_examples = collect_code_examples(root_dir)
    print(f"  Found {len(code_examples)} code examples")
    
    print("Collecting system prompts...")
    prompt_examples = collect_system_prompts(root_dir)
    print(f"  Found {len(prompt_examples)} prompt examples")
    
    print("Collecting CLI commands...")
    cli_examples = collect_cli_commands(root_dir)
    print(f"  Found {len(cli_examples)} CLI examples")
    
    all_examples = code_examples + prompt_examples + cli_examples
    
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example) + "\n")
    
    print(f"\nCreated training dataset: {output_file}")
    print(f"Total examples: {len(all_examples)}")

if __name__ == "__main__":
    root_dir = "D:/Jebat"
    output_file = "D:/Jebat/training/training_data.jsonl"
    
    create_training_dataset(root_dir, output_file)
