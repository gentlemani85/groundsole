#!/usr/bin/env python3
"""
check_integrity.py — Groundsole Workspace & Memory Integrity Linter

Performs zero-dependency deterministic validation of:
1. Markdown Link & Reference Integrity: Detects broken local file links and dead pointers.
2. Module Registry Alignment: Verifies domain modules are registered in index.md / LOAD_ORDER.md.
3. Temporal Anomaly Scan (Dreaming Assistant): Flags past dates / overdue deadlines in active focus files.

Usage:
    python check_integrity.py [--target PATH] [--strict]
"""

import sys
import os
import re
import argparse
from pathlib import Path
from datetime import date
from urllib.parse import unquote

def find_markdown_links(content):
    """
    Extracts all local relative markdown links: [label](target)
    Ignores external URLs (http, https, mailto, etc.) and pure in-page anchors (#).
    """
    pattern = r'(?:!?)\[([^\]]*)\]\(([^)]+)\)'
    links = []
    for match in re.finditer(pattern, content):
        target = match.group(2).strip()
        # Strip title only if quoted: (target "title") or (target 'title')
        title_match = re.match(r'^(.*?)\s+["\'].*?["\']$', target)
        if title_match:
            target = title_match.group(1).strip()
        
        if re.match(r'^(https?://|mailto:|conversation://|ftp://)', target, re.IGNORECASE):
            continue
        if target.startswith('#'):
            continue
        
        clean_target = target.split('#', 1)[0]
        if not clean_target:
            continue
            
        links.append(clean_target)
    return links

def check_link_target(source_file, target_link, root_dir):
    """
    Validates whether target_link resolves to an existing file on disk.
    Handles relative paths, absolute paths within workspace, and URI schemes (file://).
    Also supports cross-platform workspace aliases (e.g. Mac ~/Documents vs Windows iCloud).
    """
    decoded_target = unquote(target_link)
    
    # Strip file:/// scheme
    if decoded_target.startswith('file:///'):
        decoded_target = decoded_target[8:]
    elif decoded_target.startswith('file://'):
        decoded_target = decoded_target[7:]
        
    normalized = decoded_target.replace('\\', '/').lstrip('/')
    
    # Locate actual workspace root (containing 00_MEMORY or memory)
    ws_root = next((p for p in [root_dir] + list(root_dir.parents) if (p / "00_MEMORY").exists() or (p / "memory").exists()), root_dir)
    ws_name = ws_root.name
    
    # Dynamic workspace relative resolution if link contains workspace directory name
    if ws_name in normalized:
        rel_to_ws = normalized.split(ws_name, 1)[1].lstrip('/')
        if (ws_root / rel_to_ws).exists():
            return True

    # Standard path checks
    p = Path(decoded_target)
    if p.exists():
        return True
        
    # Relative path from source_file's parent directory
    resolved = (source_file.parent / decoded_target).resolve()
    if resolved.exists():
        return True
        
    # Relative to root_dir
    resolved_root = (root_dir / decoded_target).resolve()
    if resolved_root.exists():
        return True
        
    return False

def scan_markdown_links(target_dir, include_transcripts=False):
    """
    Scans markdown files in target_dir for broken local file links.
    Skips transcripts/ by default because historical records contain past paths.
    """
    broken_links = []
    total_links = 0
    scanned_files = 0
    
    for root, _, files in os.walk(target_dir):
        # Skip git, cache, and frozen historical transcripts by default
        ignored_patterns = ['.git', '__pycache__', '.venv', 'node_modules']
        if not include_transcripts:
            ignored_patterns.extend(['transcripts', 'archive_legacy'])
            
        if any(ignored in root for ignored in ignored_patterns):
            continue
            
        for file in files:
            if not file.endswith('.md'):
                continue
                
            scanned_files += 1
            file_path = Path(root) / file
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                broken_links.append((file_path, f"<File Read Error: {e}>", "Could not open file"))
                continue
                
            links = find_markdown_links(content)
            total_links += len(links)
            
            for link in links:
                if not check_link_target(file_path, link, target_dir):
                    broken_links.append((file_path, link))
                    
    return scanned_files, total_links, broken_links

def scan_module_registry(target_dir):
    """
    Verifies that all domain modules in modules/ are mentioned in index.md or LOAD_ORDER.md.
    """
    unregistered = []
    
    candidates = [
        target_dir / "00_MEMORY" / "modules",
        target_dir / "modules",
        target_dir / "templates" / "modules"
    ]
    
    module_dir = next((c for c in candidates if c.is_dir()), None)
    if not module_dir:
        return []
        
    index_files = [
        target_dir / "00_MEMORY" / "index.md",
        target_dir / "00_MEMORY" / "LOAD_ORDER.md",
        target_dir / "templates" / "index.md",
        target_dir / "templates" / "LOAD_ORDER.md",
        target_dir / "index.md",
        target_dir / "LOAD_ORDER.md"
    ]
    
    index_content = ""
    for idx_file in index_files:
        if idx_file.is_file():
            try:
                with open(idx_file, 'r', encoding='utf-8', errors='ignore') as f:
                    index_content += f.read() + "\n"
            except Exception:
                pass
                
    for mod_file in module_dir.glob("*.md"):
        if mod_file.name in ["README.md"]:
            continue
        if mod_file.name not in index_content:
            unregistered.append(mod_file.name)
            
    return unregistered

def scan_temporal_anomalies(target_dir):
    """
    Dreaming Assistant: Scans active state files (DYNAMIC_STATE.md) for past dates/deadlines.
    """
    anomalies = []
    today = date.today()
    
    target_files = [
        target_dir / "00_MEMORY" / "DYNAMIC_STATE.md",
        target_dir / "DYNAMIC_STATE.md",
        target_dir / "templates" / "DYNAMIC_STATE.md"
    ]
    
    date_regex = re.compile(r'\b(202[4-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))\b')
    
    for state_file in target_files:
        if not state_file.is_file():
            continue
            
        with open(state_file, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, start=1):
                if any(kw in line.lower() for kw in ['geplant', 'next step', 'schritt', 'call', 'termin', 'deadline', 'unbonding']):
                    matches = date_regex.findall(line)
                    for d_str in matches:
                        try:
                            d_val = date.fromisoformat(d_str)
                            if d_val < today:
                                anomalies.append((state_file.name, idx, d_str, line.strip()))
                        except ValueError:
                            pass
                            
    return anomalies

def main():
    parser = argparse.ArgumentParser(description="Groundsole Integrity Linter & Dreaming Assistant")
    parser.add_argument("--target", default=".", help="Root directory to inspect (default: current directory)")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero status on warnings")
    parser.add_argument("--include-transcripts", action="store_true", help="Also scan frozen historical transcripts (default: skipped)")
    args = parser.parse_args()
    
    root_dir = Path(args.target).resolve()
    print(f"🔍 Groundsole Integrity Check: {root_dir}")
    print("=" * 60)
    
    scanned_files, total_links, broken_links = scan_markdown_links(root_dir, include_transcripts=args.include_transcripts)
    print(f"📄 Markdown Files Scanned: {scanned_files}")
    print(f"🔗 Local Links Verified:    {total_links}")
    
    has_errors = False
    
    if broken_links:
        has_errors = True
        print(f"\n❌ Broken Local Links Detected ({len(broken_links)}):")
        for src, target in broken_links:
            try:
                rel_src = src.relative_to(root_dir)
            except ValueError:
                rel_src = src
            print(f"   • {rel_src} ➔ '{target}' [NOT FOUND]")
    else:
        print("✅ Link Integrity: All local markdown links resolve correctly.")
        
    unregistered_modules = scan_module_registry(root_dir)
    if unregistered_modules:
        print(f"\n⚠️  Unregistered Domain Modules ({len(unregistered_modules)}):")
        for mod in unregistered_modules:
            print(f"   • {mod} is present on disk but missing from index.md / LOAD_ORDER.md")
    else:
        print("✅ Module Registry: All domain modules are registered in memory index.")
        
    anomalies = scan_temporal_anomalies(root_dir)
    if anomalies:
        print(f"\n🌙 Dreaming Audit — Past Dates / Overdue Tasks ({len(anomalies)}):")
        for fname, line_num, d_str, line in anomalies:
            print(f"   • [{fname}:{line_num}] Past date {d_str}: \"{line[:80]}{'...' if len(line) > 80 else ''}\"")
    else:
        print("✅ Dreaming Audit: No past dates or overdue milestones in active focus.")
        
    print("=" * 60)
    
    if has_errors:
        print("❌ Integrity check failed. Please resolve broken pointers.")
        sys.exit(1)
    elif unregistered_modules and args.strict:
        print("⚠️ Strict mode: Unregistered modules detected.")
        sys.exit(2)
    else:
        print("✨ Repository and Memory Core are structurally sound.")
        sys.exit(0)

if __name__ == "__main__":
    main()
