#!/usr/bin/env python3
"""
extract_content.py - Zero-hallucination content extractor for Hugo migration

This script extracts content from ffmpeg.org source files and converts them
to Hugo-compatible markdown files. Key principles:

1. NO MODIFICATIONS to HTML content - byte-for-byte preservation
2. Only add Hugo frontmatter (TOML format)
3. Verify checksums to ensure no hallucination
4. Output structured for diff verification

Usage:
  ./extract_content.py <page_name> <output_dir>
  ./extract_content.py about hugo-site/content
  ./extract_content.py all hugo-site/content  # Extract all pages
"""

import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import json


def sha256_bytes(data: bytes) -> str:
    """Calculate SHA256 checksum of bytes"""
    return hashlib.sha256(data).hexdigest()


def extract_page(page_name: str, src_dir: Path) -> Dict[str, any]:
    """
    Extract a single page's content with zero hallucination

    Returns:
      - title: Page title (string)
      - content: HTML content (bytes, unchanged)
      - js_includes: JavaScript includes (string)
      - checksums: SHA256 hashes for verification
    """
    page_file = src_dir / page_name
    title_file = src_dir / f"{page_name}_title"
    js_file = src_dir / f"{page_name}_js"

    # Read title (text)
    if not title_file.exists():
        raise FileNotFoundError(f"Title file not found: {title_file}")
    title = title_file.read_text(encoding='utf-8').strip()

    # Read content (binary for checksum verification)
    if not page_file.exists():
        raise FileNotFoundError(f"Content file not found: {page_file}")
    content_bytes = page_file.read_bytes()

    # Read JS includes if present (text)
    js_content = ""
    if js_file.exists():
        js_content = js_file.read_text(encoding='utf-8').strip()

    return {
        "name": page_name,
        "title": title,
        "content": content_bytes,
        "js_includes": js_content,
        "checksums": {
            "title": sha256_bytes(title.encode('utf-8')),
            "content": sha256_bytes(content_bytes),
            "js": sha256_bytes(js_content.encode('utf-8'))
        }
    }


def generate_hugo_frontmatter(page_data: Dict) -> str:
    """
    Generate Hugo frontmatter in TOML format

    Frontmatter includes:
    - title: Page title
    - type: Content type (for layout selection)
    - checksums: For verification
    - js_includes: Custom JavaScript if any
    """
    name = page_data["name"]
    title = page_data["title"]
    js = page_data["js_includes"]
    checksums = page_data["checksums"]

    # Escape quotes in title if present
    title_escaped = title.replace('"', '\\"')

    frontmatter = "+++\n"
    frontmatter += f'title = "{title_escaped}"\n'
    frontmatter += f'slug = "{name}"\n'

    # Special handling for index page
    if name == "index":
        frontmatter += 'type = "homepage"\n'
    else:
        frontmatter += 'type = "page"\n'

    # Add JS includes if present
    if js:
        js_escaped = js.replace('"', '\\"').replace('\n', '\\n')
        frontmatter += f'js_includes = "{js_escaped}"\n'

    # Add checksums for verification
    frontmatter += '\n[checksums]\n'
    frontmatter += f'content = "{checksums["content"]}"\n'
    frontmatter += f'title = "{checksums["title"]}"\n'
    frontmatter += f'js = "{checksums["js"]}"\n'

    frontmatter += "+++\n\n"

    return frontmatter


def write_hugo_content(page_data: Dict, output_dir: Path) -> Path:
    """
    Write Hugo markdown file with HTML content preserved

    Format:
    +++
    title = "Page Title"
    slug = "pagename"
    type = "page"
    [checksums]
    content = "sha256..."
    +++

    <original HTML content unchanged>
    """
    name = page_data["name"]

    # Generate frontmatter
    frontmatter = generate_hugo_frontmatter(page_data)

    # Get content as string (decode from bytes)
    content_str = page_data["content"].decode('utf-8')

    # Combine frontmatter + content
    full_content = frontmatter + content_str

    # Determine output filename
    if name == "index":
        output_file = output_dir / "_index.md"
    else:
        output_file = output_dir / f"{name}.md"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write file
    output_file.write_text(full_content, encoding='utf-8')

    return output_file


def main():
    """Main extraction function"""
    if len(sys.argv) < 3:
        print("Usage: extract_content.py <page_name|all> <output_dir>")
        print("\nExamples:")
        print("  extract_content.py about hugo-site/content")
        print("  extract_content.py all hugo-site/content")
        return 1

    page_name = sys.argv[1]
    output_dir = Path(sys.argv[2])

    base_dir = Path("/home/user/ffmpeg-web")
    src_dir = base_dir / "src"

    # Load page list from inventory
    inventory_file = base_dir / "site_inventory.json"
    if not inventory_file.exists():
        print("ERROR: site_inventory.json not found. Run analyze_site.py first.")
        return 1

    inventory = json.loads(inventory_file.read_text())
    all_pages = inventory["makefile"]["pages"]

    # Determine which pages to extract
    if page_name == "all":
        pages_to_extract = all_pages
    elif page_name in all_pages:
        pages_to_extract = [page_name]
    else:
        print(f"ERROR: Page '{page_name}' not found in Makefile SRCS")
        print(f"Available pages: {', '.join(all_pages)}")
        return 1

    # Extract and write each page
    results = []
    for page in pages_to_extract:
        try:
            print(f"Extracting: {page}...")
            page_data = extract_page(page, src_dir)
            output_file = write_hugo_content(page_data, output_dir)
            results.append({
                "page": page,
                "status": "success",
                "output": str(output_file),
                "checksums": page_data["checksums"]
            })
            print(f"  ✓ Written to: {output_file}")
        except Exception as e:
            results.append({
                "page": page,
                "status": "error",
                "error": str(e)
            })
            print(f"  ✗ Error: {e}")

    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n{'='*60}")
    print(f"Extraction complete: {success_count}/{len(pages_to_extract)} successful")

    # Write extraction report
    report_file = base_dir / "extraction_report.json"
    report_file.write_text(json.dumps({
        "extraction": {
            "pages_requested": len(pages_to_extract),
            "pages_successful": success_count,
            "output_dir": str(output_dir)
        },
        "results": results
    }, indent=2))
    print(f"Report written to: {report_file}")

    return 0 if success_count == len(pages_to_extract) else 1


if __name__ == "__main__":
    exit(main())
