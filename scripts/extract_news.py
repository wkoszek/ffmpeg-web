#!/usr/bin/env python3
"""
extract_news.py - Extract news entries from index page into individual Markdown files

This script parses the index page and extracts each news entry (<h3> + content)
into individual markdown files for Hugo, converting HTML to proper Markdown.

Usage:
  ./extract_news.py <index_file> <output_dir> [--html]
  ./extract_news.py src/index hugo-site/content/news
  ./extract_news.py src/index hugo-site/content/news --html  # Keep as HTML
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from lxml import html as lxml_html, etree
import hashlib

# html2text is optional - if not installed, will output HTML instead
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False


def parse_date(date_str):
    """
    Parse date from various formats like:
    - "August 22nd, 2025"
    - "September 30th, 2024"
    - "June 2nd, 2024"

    Returns datetime object and ISO date string
    """
    # Remove ordinal suffixes (st, nd, rd, th)
    date_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    try:
        dt = datetime.strptime(date_clean, '%B %d, %Y')
        return dt, dt.strftime('%Y-%m-%d')
    except ValueError:
        # Try alternate format
        try:
            dt = datetime.strptime(date_clean, '%b %d, %Y')
            return dt, dt.strftime('%Y-%m-%d')
        except:
            return None, date_str


def html_to_markdown(html_content):
    """
    Convert HTML to Markdown

    Uses html2text library with FFmpeg-friendly settings:
    - No wrapping (preserve line breaks as in original)
    - Keep links inline
    - Preserve code blocks
    - Don't escape special characters unnecessarily
    """
    h = html2text.HTML2Text()

    # Configure html2text for clean output
    h.body_width = 0  # No wrapping
    h.unicode_snob = True  # Use unicode characters
    h.ignore_links = False  # Keep links
    h.ignore_images = False  # Keep images
    h.ignore_emphasis = False  # Keep bold/italic
    h.skip_internal_links = False  # Keep anchor links
    h.inline_links = True  # Use inline link style [text](url)
    h.protect_links = True  # Don't wrap URLs
    h.wrap_links = False  # Don't wrap link text

    # Convert
    markdown = h.handle(html_content)

    # Clean up common issues
    markdown = markdown.strip()

    # Remove excessive blank lines (more than 2 in a row)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    return markdown


def extract_news_entries(index_file):
    """
    Extract all news entries from index page

    Returns list of dicts with:
    - id: h3 id attribute
    - title: Full title text
    - date_str: Original date string
    - date_iso: ISO format date
    - content_html: HTML content (all elements until next h3)
    """
    content = index_file.read_text(encoding='utf-8')
    tree = lxml_html.fromstring(content)

    # Find all h3 tags with id attributes (news entries)
    news_h3s = tree.xpath('//h3[@id]')

    entries = []

    for i, h3 in enumerate(news_h3s):
        entry_id = h3.get('id')

        # Get full title text (including spans)
        title_text = ''.join(h3.itertext()).strip()

        # Try to parse date from title
        # Pattern: "Month Day(st/nd/rd/th), Year, Title" or "Month Day, Year, Title"
        date_match = re.match(
            r'([A-Z][a-z]+\s+\d+(?:st|nd|rd|th)?,\s+\d{4}),?\s*(.*)',
            title_text
        )

        if date_match:
            date_str = date_match.group(1)
            title_part = date_match.group(2).strip()
            dt, date_iso = parse_date(date_str)
        else:
            date_str = None
            title_part = title_text
            dt = None
            date_iso = None

        # Extract content: all elements between this h3 and next h3 (or end)
        content_elements = []

        # Get next sibling elements until we hit another h3 or run out
        current = h3.getnext()
        while current is not None:
            # Stop at next h3 with id (next news entry)
            if current.tag == 'h3' and current.get('id'):
                break

            # Stop at h1 (like "Older entries are in the news archive")
            if current.tag == 'h1':
                break

            content_elements.append(current)
            current = current.getnext()

        # Serialize content to HTML
        content_html = '\n'.join(
            lxml_html.tostring(elem, encoding='unicode', method='html')
            for elem in content_elements
        ).strip()

        entries.append({
            'id': entry_id,
            'title_full': title_text,
            'title': title_part,
            'date_str': date_str,
            'date_iso': date_iso,
            'datetime': dt,
            'content_html': content_html,
            'index': i
        })

    return entries


def create_news_markdown(entry, output_dir, keep_html=False):
    """
    Create a markdown file for a news entry

    Filename format: YYYY-MM-DD-slug.md or index-slug.md if no date

    Args:
        entry: News entry dict
        output_dir: Output directory path
        keep_html: If True, keep content as HTML; if False, convert to Markdown
    """
    # Generate slug from id
    slug = entry['id']

    # Determine filename
    if entry['date_iso']:
        filename = f"{entry['date_iso']}-{slug}.md"
    else:
        # No date, use index
        filename = f"{entry['index']:03d}-{slug}.md"

    filepath = output_dir / filename

    # Escape quotes in title for YAML
    title_escaped = entry["title_full"].replace('"', '\\"')

    # Generate YAML frontmatter
    frontmatter = "---\n"
    frontmatter += f'title: "{title_escaped}"\n'

    if entry['date_iso']:
        frontmatter += f'date: {entry["date_iso"]}T00:00:00Z\n'

    frontmatter += f'slug: {slug}\n'
    frontmatter += 'type: news\n'

    # Add original date string if present
    if entry['date_str']:
        frontmatter += f'date_display: "{entry["date_str"]}"\n'

    # Checksum for verification (always of original HTML)
    content_hash = hashlib.sha256(entry['content_html'].encode('utf-8')).hexdigest()
    frontmatter += f'checksum_html: {content_hash}\n'

    frontmatter += "---\n\n"

    # Convert content
    if keep_html:
        content = entry['content_html']
    else:
        content = html_to_markdown(entry['content_html'])

    # Combine frontmatter + content
    full_content = frontmatter + content

    # Write file
    filepath.write_text(full_content, encoding='utf-8')

    return filepath


def main():
    if len(sys.argv) < 3:
        print("Usage: extract_news.py <index_file> <output_dir> [--html]")
        print("\nExamples:")
        print("  extract_news.py src/index hugo-site/content/news")
        print("  extract_news.py src/index hugo-site/content/news --html  # Keep as HTML")
        return 1

    index_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    keep_html = '--html' in sys.argv

    if not index_file.exists():
        print(f"Error: Index file not found: {index_file}")
        return 1

    # Check for html2text if Markdown conversion requested
    if not keep_html and not HAS_HTML2TEXT:
        print("Warning: html2text module not found.")
        print("Install it with: pip3 install html2text")
        print("Falling back to HTML output (same as --html flag)")
        print()
        keep_html = True

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    format_mode = "HTML" if keep_html else "Markdown"
    print(f"Extracting news entries from {index_file}...")
    print(f"Output format: {format_mode}")

    entries = extract_news_entries(index_file)

    print(f"Found {len(entries)} news entries")
    print(f"{'='*60}")

    # Create markdown files
    for entry in entries:
        filepath = create_news_markdown(entry, output_dir, keep_html=keep_html)

        date_display = entry['date_str'] or f"Entry {entry['index']}"
        print(f"  ✓ {date_display}")
        print(f"    → {filepath.name}")

    print(f"{'='*60}")
    print(f"Extraction complete: {len(entries)} files created")
    print(f"Output directory: {output_dir}")

    # Print summary statistics
    with_dates = sum(1 for e in entries if e['date_iso'])
    without_dates = len(entries) - with_dates

    print(f"\nStatistics:")
    print(f"  Entries with dates: {with_dates}")
    print(f"  Entries without dates: {without_dates}")
    print(f"  Format: {format_mode}")

    if entries:
        # Find date range
        dated_entries = [e for e in entries if e['datetime']]
        if dated_entries:
            dates = [e['datetime'] for e in dated_entries]
            print(f"  Date range: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")

    return 0


if __name__ == "__main__":
    exit(main())
