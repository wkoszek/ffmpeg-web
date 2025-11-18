#!/usr/bin/env python3
"""
verify_html.py - HTML verification and diff tool

This script compares original (Makefile-generated) HTML with Hugo-generated HTML
to ensure byte-for-byte equivalence or identify specific differences.

Usage:
  ./verify_html.py <original_dir> <hugo_dir> [page_name]
  ./verify_html.py htdocs hugo-site/public about
  ./verify_html.py htdocs hugo-site/public  # Compare all pages

Features:
- Normalized HTML comparison (handles whitespace differences)
- Line-by-line diffing
- Summary statistics
- Checksum verification
"""

import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
import difflib
from lxml import html as lxml_html, etree


def sha256_file(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def normalize_html(html_str: str) -> str:
    """
    Normalize HTML for comparison

    - Parse and re-serialize to normalize whitespace
    - Remove extra blank lines
    - Normalize indentation
    """
    try:
        # Parse HTML
        tree = lxml_html.fromstring(html_str)

        # Serialize back to HTML
        normalized = lxml_html.tostring(
            tree,
            encoding='unicode',
            method='html',
            pretty_print=False
        )

        return normalized
    except Exception as e:
        # If parsing fails, return original
        print(f"Warning: HTML normalization failed: {e}")
        return html_str


def compare_html_files(original_path: Path, hugo_path: Path) -> Dict:
    """
    Compare two HTML files

    Returns dict with:
    - identical: bool (exact match)
    - normalized_identical: bool (match after normalization)
    - diff_lines: int (number of differing lines)
    - diff_output: str (unified diff if different)
    """
    if not original_path.exists():
        return {
            "error": f"Original file not found: {original_path}",
            "identical": False
        }

    if not hugo_path.exists():
        return {
            "error": f"Hugo file not found: {hugo_path}",
            "identical": False
        }

    # Read files
    original_content = original_path.read_text(encoding='utf-8')
    hugo_content = hugo_path.read_text(encoding='utf-8')

    # Calculate checksums
    original_sha = sha256_file(original_path)
    hugo_sha = sha256_file(hugo_path)

    result = {
        "original_path": str(original_path),
        "hugo_path": str(hugo_path),
        "original_sha256": original_sha,
        "hugo_sha256": hugo_sha,
        "original_size": len(original_content),
        "hugo_size": len(hugo_content),
        "identical": original_sha == hugo_sha
    }

    if result["identical"]:
        result["status"] = "EXACT_MATCH"
        return result

    # Try normalized comparison
    try:
        original_normalized = normalize_html(original_content)
        hugo_normalized = normalize_html(hugo_content)

        result["normalized_identical"] = (original_normalized == hugo_normalized)

        if result["normalized_identical"]:
            result["status"] = "NORMALIZED_MATCH"
            return result
    except:
        result["normalized_identical"] = False

    # Generate diff
    original_lines = original_content.splitlines(keepends=True)
    hugo_lines = hugo_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        original_lines,
        hugo_lines,
        fromfile=f"original/{original_path.name}",
        tofile=f"hugo/{hugo_path.name}",
        lineterm=''
    ))

    result["status"] = "DIFFERENT"
    result["diff_lines"] = len([l for l in diff if l.startswith('+') or l.startswith('-')])
    result["diff_output"] = '\n'.join(diff[:100])  # Limit diff output

    return result


def compare_pages(original_dir: Path, hugo_dir: Path, page_names: List[str]) -> List[Dict]:
    """Compare multiple pages"""
    results = []

    for page in page_names:
        original_file = original_dir / f"{page}.html"
        hugo_file = hugo_dir / f"{page}.html"

        print(f"Comparing: {page}.html...")
        result = compare_html_files(original_file, hugo_file)
        result["page"] = page
        results.append(result)

        # Print status
        status = result.get("status", "ERROR")
        if status == "EXACT_MATCH":
            print(f"  ✓ EXACT MATCH")
        elif status == "NORMALIZED_MATCH":
            print(f"  ~ NORMALIZED MATCH (whitespace differences)")
        elif status == "DIFFERENT":
            print(f"  ✗ DIFFERENT ({result.get('diff_lines', '?')} diff lines)")
        else:
            print(f"  ✗ ERROR: {result.get('error', 'Unknown error')}")

    return results


def print_summary(results: List[Dict]):
    """Print comparison summary"""
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")

    total = len(results)
    exact_matches = sum(1 for r in results if r.get("status") == "EXACT_MATCH")
    normalized_matches = sum(1 for r in results if r.get("status") == "NORMALIZED_MATCH")
    different = sum(1 for r in results if r.get("status") == "DIFFERENT")
    errors = sum(1 for r in results if "error" in r)

    print(f"Total pages compared: {total}")
    print(f"  Exact matches:      {exact_matches}")
    print(f"  Normalized matches: {normalized_matches}")
    print(f"  Different:          {different}")
    print(f"  Errors:             {errors}")

    if different > 0:
        print(f"\nPages with differences:")
        for r in results:
            if r.get("status") == "DIFFERENT":
                print(f"  - {r['page']}.html ({r.get('diff_lines', '?')} diff lines)")

    print(f"{'='*60}")

    # Return exit code
    return 0 if (different == 0 and errors == 0) else 1


def main():
    """Main verification function"""
    if len(sys.argv) < 3:
        print("Usage: verify_html.py <original_dir> <hugo_dir> [page_name]")
        print("\nExamples:")
        print("  verify_html.py htdocs hugo-site/public about")
        print("  verify_html.py htdocs hugo-site/public  # Compare all")
        return 1

    original_dir = Path(sys.argv[1])
    hugo_dir = Path(sys.argv[2])

    if not original_dir.exists():
        print(f"ERROR: Original directory not found: {original_dir}")
        return 1

    if not hugo_dir.exists():
        print(f"ERROR: Hugo directory not found: {hugo_dir}")
        return 1

    # Determine which pages to compare
    if len(sys.argv) >= 4:
        # Single page specified
        page_names = [sys.argv[3]]
    else:
        # Compare all pages - find all HTML files in original dir
        html_files = list(original_dir.glob("*.html"))
        page_names = [f.stem for f in html_files]
        page_names.sort()

    # Run comparison
    results = compare_pages(original_dir, hugo_dir, page_names)

    # Print summary
    exit_code = print_summary(results)

    # Write detailed results to file
    import json
    results_file = Path("verification_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "comparison": {
                "original_dir": str(original_dir),
                "hugo_dir": str(hugo_dir),
                "pages_compared": len(results)
            },
            "results": results
        }, f, indent=2)

    print(f"\nDetailed results written to: {results_file}")

    return exit_code


if __name__ == "__main__":
    exit(main())
