#!/usr/bin/env python3
"""
analyze_site.py - Forensic analysis of ffmpeg.org site structure

This script performs read-only analysis of the current site:
- Catalogs all source files
- Extracts metadata (titles, JS includes)
- Calculates checksums for verification
- Outputs structured JSON (no interpretation, just facts)

Zero-hallucination guarantee: Only reads files, no modifications.
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any
from lxml import html as lxml_html


def sha256_file(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def analyze_page(page_name: str, src_dir: Path) -> Dict[str, Any]:
    """
    Analyze a single page's source files

    Returns factual data only:
    - File sizes
    - Checksums
    - Title content
    - JS includes
    - HTML structure metadata
    """
    page_file = src_dir / page_name
    title_file = src_dir / f"{page_name}_title"
    js_file = src_dir / f"{page_name}_js"

    page_data = {
        "name": page_name,
        "files": {}
    }

    # Analyze main content file
    if page_file.exists():
        content = page_file.read_bytes()
        page_data["files"]["content"] = {
            "path": str(page_file),
            "size_bytes": len(content),
            "sha256": sha256_file(page_file),
            "exists": True
        }

        # Parse HTML to extract structural metadata (read-only)
        try:
            tree = lxml_html.fromstring(content)
            page_data["html_metadata"] = {
                "root_element": tree.tag if hasattr(tree, 'tag') else None,
                "element_count": len(tree.xpath('//*')),
                "has_images": len(tree.xpath('//img')) > 0,
                "has_links": len(tree.xpath('//a')) > 0,
                "has_headings": len(tree.xpath('//h1|//h2|//h3|//h4|//h5|//h6')) > 0,
            }
        except Exception as e:
            page_data["html_metadata"] = {
                "parse_error": str(e)
            }
    else:
        page_data["files"]["content"] = {"exists": False}

    # Analyze title file
    if title_file.exists():
        title_content = title_file.read_text(encoding='utf-8').strip()
        page_data["files"]["title"] = {
            "path": str(title_file),
            "size_bytes": title_file.stat().st_size,
            "sha256": sha256_file(title_file),
            "content": title_content,
            "exists": True
        }
    else:
        page_data["files"]["title"] = {"exists": False}

    # Analyze JS includes file
    if js_file.exists():
        js_content = js_file.read_text(encoding='utf-8').strip()
        page_data["files"]["js"] = {
            "path": str(js_file),
            "size_bytes": js_file.stat().st_size,
            "sha256": sha256_file(js_file),
            "content": js_content,
            "has_content": len(js_content) > 0,
            "exists": True
        }
    else:
        page_data["files"]["js"] = {"exists": False}

    return page_data


def analyze_templates(src_dir: Path) -> Dict[str, Any]:
    """Analyze template files"""
    templates = {}

    template_files = [
        "template_head1",
        "template_head2",
        "template_head3",
        "template_head_prod",
        "template_head_dev",
        "template_footer1",
        "template_footer2",
        "template_footer_prod",
        "template_footer_dev"
    ]

    for template_name in template_files:
        template_path = src_dir / template_name
        if template_path.exists():
            content = template_path.read_bytes()
            templates[template_name] = {
                "path": str(template_path),
                "size_bytes": len(content),
                "sha256": sha256_file(template_path),
                "exists": True,
                "line_count": len(template_path.read_text(encoding='utf-8').splitlines())
            }
        else:
            templates[template_name] = {"exists": False}

    return templates


def analyze_makefile(makefile_path: Path) -> Dict[str, Any]:
    """Extract facts from Makefile"""
    if not makefile_path.exists():
        return {"exists": False}

    content = makefile_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    # Extract SRCS list (page names) - handle continuation lines
    srcs_lines = []
    in_srcs = False
    for line in lines:
        if line.startswith('SRCS'):
            in_srcs = True
            srcs_lines.append(line)
        elif in_srcs:
            if line.strip() and not line.startswith('#'):
                # Check if previous line had continuation
                if srcs_lines[-1].rstrip().endswith('\\'):
                    srcs_lines.append(line)
                else:
                    break
            else:
                break

    pages = []
    if srcs_lines:
        # Join all lines and extract page names
        full_line = ' '.join(srcs_lines)
        # Remove SRCS = and backslashes
        full_line = full_line.replace('SRCS', '').replace('=', '').replace('\\', '')
        pages = full_line.split()

    return {
        "path": str(makefile_path),
        "size_bytes": makefile_path.stat().st_size,
        "sha256": sha256_file(makefile_path),
        "pages": pages,
        "page_count": len(pages),
        "exists": True
    }


def main():
    """Main analysis function"""
    base_dir = Path("/home/user/ffmpeg-web")
    src_dir = base_dir / "src"
    makefile_path = base_dir / "Makefile"

    # Start with Makefile to get authoritative page list
    makefile_data = analyze_makefile(makefile_path)

    if not makefile_data.get("exists"):
        print(json.dumps({"error": "Makefile not found"}, indent=2))
        return 1

    pages = makefile_data["pages"]

    # Build complete inventory
    inventory = {
        "analysis_metadata": {
            "script": "analyze_site.py",
            "purpose": "Zero-hallucination site structure analysis",
            "base_dir": str(base_dir),
            "src_dir": str(src_dir)
        },
        "makefile": makefile_data,
        "templates": analyze_templates(src_dir),
        "pages": {}
    }

    # Analyze each page
    for page_name in pages:
        inventory["pages"][page_name] = analyze_page(page_name, src_dir)

    # Summary statistics
    inventory["summary"] = {
        "total_pages": len(pages),
        "pages_with_content": sum(1 for p in inventory["pages"].values()
                                   if p["files"]["content"].get("exists")),
        "pages_with_title": sum(1 for p in inventory["pages"].values()
                                 if p["files"]["title"].get("exists")),
        "pages_with_js": sum(1 for p in inventory["pages"].values()
                              if p["files"]["js"].get("exists") and
                                 p["files"]["js"].get("has_content")),
        "templates_found": sum(1 for t in inventory["templates"].values()
                               if t.get("exists"))
    }

    # Output JSON (diffable, no interpretation)
    print(json.dumps(inventory, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    exit(main())
