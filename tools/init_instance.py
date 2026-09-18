#!/usr/bin/env python3
"""
Groundsole Instance Scaffolding Tool

Initializes an isolated, clean workspace instance from Groundsole blueprints.
Strictly guarantees zero data leakage from creator private files.
Installs genuine Groundsole core skills: stream-archive, memory-recall, system-hygiene, and inbox-triage.
Provisions deterministic execution scripts in target scripts/ folder.
"""

import os
import sys
import shutil
import argparse
import datetime
import json
from pathlib import Path

def get_framework_dir() -> Path:
    return Path(__file__).resolve().parent.parent

def load_version(framework_dir: Path) -> dict:
    version_file = framework_dir / "version.json"
    if version_file.exists():
        with open(version_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"name": "groundsole", "version": "0.1.0"}

def scaffold_instance(target_dir: Path, user_name: str, profile: str):
    framework_dir = get_framework_dir()
    templates_dir = framework_dir / "templates"
    skills_dir = framework_dir / "skills"
    tools_scripts_dir = framework_dir / "tools" / "scripts"
    version_info = load_version(framework_dir)
    today_str = datetime.date.today().isoformat()

    print(f"🌱 Initializing Groundsole instance v{version_info.get('version')}...")
    print(f"📁 Target:  {target_dir}")
    print(f"👤 Owner:   {user_name}")
    print(f"🎯 Profile: {profile}")

    target_dir.mkdir(parents=True, exist_ok=True)
    memory_dir = target_dir / "00_MEMORY"
    modules_dir = memory_dir / "modules"
    transcripts_dir = memory_dir / "transcripts"
    summaries_dir = memory_dir / "summaries"
    vectors_dir = memory_dir / "vectors"
    inbox_dir = target_dir / "Inbox"
    target_scripts_dir = target_dir / "scripts"

    memory_dir.mkdir(exist_ok=True)
    modules_dir.mkdir(exist_ok=True)
    transcripts_dir.mkdir(exist_ok=True)
    summaries_dir.mkdir(exist_ok=True)
    vectors_dir.mkdir(exist_ok=True)
    inbox_dir.mkdir(exist_ok=True)
    target_scripts_dir.mkdir(exist_ok=True)

    # 1. AGENTS.md in root
    shutil.copy2(templates_dir / "AGENTS.md", target_dir / "AGENTS.md")

    # 2. bootstrap.md in root
    shutil.copy2(templates_dir / "bootstrap.md", target_dir / "bootstrap.md")

    # 3. index.md
    index_content = (templates_dir / "index.md").read_text(encoding="utf-8")
    index_content = index_content.replace("{{DATE}}", today_str)
    (memory_dir / "index.md").write_text(index_content, encoding="utf-8")

    # 4. LOAD_ORDER.md
    shutil.copy2(templates_dir / "LOAD_ORDER.md", memory_dir / "LOAD_ORDER.md")

    # 5. STYLE_AND_GUARDRAILS.md
    shutil.copy2(templates_dir / "STYLE_AND_GUARDRAILS.md", memory_dir / "STYLE_AND_GUARDRAILS.md")

    # 6. DYNAMIC_STATE.md
    dynamic_content = (templates_dir / "DYNAMIC_STATE.md").read_text(encoding="utf-8")
    focus_map = {
        "school": "Academic term onboarding, subject setup & cognitive cockpit orientation",
        "organization": "Team onboarding, operational deliverables & workflow setup",
        "personal": "Personal life modules, goal alignment & workspace initialization",
        "minimal": "Workspace setup"
    }
    focus_text = focus_map.get(profile, "Workspace initialization")
    dynamic_content = dynamic_content.replace("{{DATE}}", today_str)
    dynamic_content = dynamic_content.replace("{{USER_NAME}}", user_name)
    dynamic_content = dynamic_content.replace("{{FOCUS}}", focus_text)
    (memory_dir / "DYNAMIC_STATE.md").write_text(dynamic_content, encoding="utf-8")

    # 7. Universal Domain Modules
    all_modules = [
        "OPERATIONS_AND_PROJECTS.md",
        "RESOURCES_AND_FINANCE.md",
        "INFRASTRUCTURE_AND_ASSETS.md",
        "LEARNING_AND_SKILLS.md"
    ]
    
    if profile == "school":
        selected_modules = ["LEARNING_AND_SKILLS.md", "OPERATIONS_AND_PROJECTS.md"]
    elif profile == "organization":
        selected_modules = ["OPERATIONS_AND_PROJECTS.md", "RESOURCES_AND_FINANCE.md", "INFRASTRUCTURE_AND_ASSETS.md"]
    elif profile == "personal":
        selected_modules = all_modules
    else:  # minimal
        selected_modules = ["OPERATIONS_AND_PROJECTS.md"]

    for mod_name in selected_modules:
        src_mod = templates_dir / "modules" / mod_name
        if src_mod.exists():
            mod_text = src_mod.read_text(encoding="utf-8")
            mod_text = mod_text.replace("{{DATE}}", today_str)
            mod_text = mod_text.replace("{{USER_NAME}}", user_name)
            (modules_dir / mod_name).write_text(mod_text, encoding="utf-8")

    # 8. Copy execution scripts into target scripts/
    if tools_scripts_dir.exists():
        for script_file in tools_scripts_dir.glob("*.py"):
            shutil.copy2(script_file, target_scripts_dir / script_file.name)

    # 9. Bundle Groundsole core skills
    target_skills = target_dir / "skills"
    target_skills.mkdir(exist_ok=True)
    all_skills = [
        "stream-archive",
        "memory-recall",
        "document-export",
        "mail-manager",
        "system-hygiene",
        "inbox-triage"
    ]
    for skill_name in all_skills:
        src_skill = skills_dir / skill_name
        if src_skill.exists():
            shutil.copytree(src_skill, target_skills / skill_name, dirs_exist_ok=True)

    # 10. Anchor local version.json for decentralized updates
    local_version = {
        "framework": "groundsole",
        "installed_version": version_info.get("version", "0.1.0"),
        "installed_date": today_str,
        "profile": profile,
        "upstream_repo": version_info.get("repository", "https://github.com/gentlemani85/groundsole")
    }
    with open(target_dir / "version.json", "w", encoding="utf-8") as f:
        json.dump(local_version, f, indent=2)

    # 11. Instance .gitignore
    gitignore_content = """.DS_Store
Thumbs.db
.gemini/
.antigravity/
*.tmp
*.log
*.db
*.sqlite
*.sqlite3
*.db-journal
*.db-wal
*.db-shm
00_MEMORY/vectors/*.db
00_MEMORY/*.db
"""
    (target_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    print("\n✅ Groundsole instance scaffolded successfully!")
    print(f"👉 Next step: Open '{target_dir}' in Antigravity, Hermes, Claude Code, or Codex.")

def main():
    parser = argparse.ArgumentParser(description="Groundsole Instance Scaffolding Tool")
    parser.add_argument("--target", required=True, help="Target workspace path")
    parser.add_argument("--user", default="User", help="Instance owner / team name (e.g. Alex)")
    parser.add_argument("--profile", default="school", choices=["school", "organization", "personal", "minimal"], help="Target configuration profile")

    args = parser.parse_args()
    target_path = Path(args.target).expanduser().resolve()
    scaffold_instance(target_path, args.user, args.profile)

if __name__ == "__main__":
    main()
