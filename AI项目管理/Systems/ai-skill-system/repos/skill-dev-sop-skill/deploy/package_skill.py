#!/usr/bin/env python3
"""
Skill 工程包打包脚本
生成 skill-dev-sop-v[version].skill 文件
"""
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

SKILL_NAME = "skill-dev-sop"
VERSION = "1.0.0"
OUTPUT_FILE = f"{SKILL_NAME}-v{VERSION}.skill"

# 打包文件清单
INCLUDE_FILES = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "core/system-prompt-full.md",
    "core/system-prompt-lite.md",
    "core/activation-card.md",
    "sub-skills/01-value-mining.md",
    "sub-skills/02-direction-decision.md",
    "sub-skills/03-engineering-build.md",
    "sub-skills/04-simulation-test.md",
    "sub-skills/05-autonomous-iteration.md",
    "sub-skills/06-user-guide.md",
    "sub-skills/07-skill-packaging.md",
    "sub-skills/08-github-publish.md",
    "sub-skills/09-install-prompts.md",
    "sub-skills/10-global-install.md",
    "deploy/deploy-universal.md",
    "docs/changelog.md",
    "docs/design-principles.md",
]

def main():
    # 切换到工程包根目录
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    print(f"打包 {SKILL_NAME} v{VERSION}...")
    print(f"工作目录: {os.getcwd()}")
    print()

    # 生成 manifest.json
    manifest = {
        "name": SKILL_NAME,
        "version": VERSION,
        "packaged_at": datetime.now().isoformat(),
        "author": "letplaylimited-MARK",
        "description": "AI Skill 开发工作流 SOP 工程师",
        "files": INCLUDE_FILES
    }

    missing_files = []
    included_files = []

    with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 写入 manifest
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        print("  ✅ manifest.json")

        # 打包核心文件
        for file_path in INCLUDE_FILES:
            if os.path.exists(file_path):
                zf.write(file_path)
                included_files.append(file_path)
                print(f"  ✅ {file_path}")
            else:
                missing_files.append(file_path)
                print(f"  ❌ 缺失: {file_path}")

    print()
    print(f"打包完成: {OUTPUT_FILE}")
    print(f"包含: {len(included_files)} 个文件")

    if missing_files:
        print(f"缺失: {len(missing_files)} 个文件")
        for f in missing_files:
            print(f"  - {f}")
    else:
        print("所有文件已包含 ✅")

if __name__ == "__main__":
    main()
