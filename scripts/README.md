# FFmpeg Website Migration Scripts

This directory contains Python3 scripts for migrating the FFmpeg website from the Makefile-based system to Hugo.

## Scripts

### analyze_site.py

Forensic analysis of the current site structure with SHA256 checksums.

```bash
python3 analyze_site.py > site_inventory.json
```

**Output:** JSON catalog of all source files, templates, and pages with checksums.

### extract_content.py

Zero-hallucination content extractor that preserves HTML byte-for-byte.

```bash
# Extract single page
python3 extract_content.py about hugo-site/content

# Extract all pages
python3 extract_content.py all hugo-site/content
```

**Output:** Hugo markdown files with frontmatter + preserved HTML content.

### extract_news.py

Extracts individual news entries from the monolithic index page.

```bash
python3 extract_news.py src/index hugo-site/content/news
```

**Features:**
- Parses 60+ news entries from `src/index`
- Extracts dates, titles, and content automatically
- Creates individual markdown files per entry
- Filename format: `YYYY-MM-DD-slug.md`
- Preserves HTML content with checksums
- Handles various date formats

**Output:** Individual news entry files like:
- `2025-08-22-pr8.0.md` - FFmpeg 8.0 release
- `2024-09-30-pr7.1.md` - FFmpeg 7.1 release
- `2024-09-11-coverity.md` - Coverity news

### verify_html.py

HTML verification and diff tool to compare original vs Hugo output.

```bash
# Verify single page
python3 verify_html.py htdocs hugo-site/public about

# Verify all pages
python3 verify_html.py htdocs hugo-site/public
```

**Output:**
- Terminal summary (exact match / normalized match / different)
- `verification_results.json` - Detailed diff analysis

## Requirements

```bash
pip3 install lxml
```

**Why lxml?**
- C-based (libxml2) - strict, fast parsing
- Won't silently fix/modify HTML
- Used by Mozilla and other large projects
- Better for verification (errors on malformed HTML)

## Workflow

1. **Analyze** - Understand current structure
   ```bash
   python3 analyze_site.py > site_inventory.json
   ```

2. **Extract pages** - Convert to Hugo format
   ```bash
   python3 extract_content.py all hugo-site/content
   ```

3. **Extract news** - Split news entries (optional)
   ```bash
   python3 extract_news.py src/index hugo-site/content/news
   ```

4. **Build** - Generate Hugo site
   ```bash
   cd hugo-site && hugo
   ```

5. **Verify** - Check output matches original
   ```bash
   python3 verify_html.py htdocs hugo-site/public
   ```

## News Entry Structure

The `extract_news.py` script creates files with this format:

```markdown
+++
title = "August 22nd, 2025, FFmpeg 8.0 \"Huffman\""
date = 2025-08-22T00:00:00Z
slug = "pr8.0"
type = "news"
date_display = "August 22nd, 2025"

[checksums]
content = "sha256..."
+++

<p>
  A new major release, <a href="download.html#release_8.0">FFmpeg 8.0 "Huffman"</a>,
  is now available for download.
  ...
</p>
```

## Zero-Hallucination Guarantees

All scripts follow these principles:

1. **Read-only parsing** - No content modification
2. **Byte-for-byte preservation** - HTML content unchanged
3. **Checksum verification** - SHA256 hashes for all content
4. **Structured output** - JSON for diffs and inspection
5. **No AI/LLM** - Pure algorithmic extraction

## Examples

### Extract and verify a single page

```bash
# Extract
python3 extract_content.py about hugo-site/content

# Build
cd hugo-site && hugo

# Verify
cd ..
python3 verify_html.py htdocs hugo-site/public about
```

### Full migration workflow

```bash
# Build original site
make clean && make

# Generate checksums
find htdocs -name "*.html" | xargs sha256sum > checksums_original.txt

# Extract all content
python3 extract_content.py all hugo-site/content

# Extract news entries (optional - creates individual files)
python3 extract_news.py src/index hugo-site/content/news

# Build Hugo site
cd hugo-site && make rebuild

# Verify all pages
python3 ../scripts/verify_html.py ../htdocs public
```

## Troubleshooting

**lxml not found:**
```bash
pip3 install lxml
```

**Verification shows differences:**
- Expected for now - only whitespace and IE9 comments differ
- See `../MIGRATION_REPORT.md` for explanation
- Run `diff -u htdocs/page.html hugo-site/public/page.html` to inspect

**News extraction fails:**
- Check `src/index` exists and has `<h3 id="...">` tags
- Verify HTML structure with: `grep '<h3 id=' src/index`

## Future Enhancements

Potential script additions:

- `extract_archive.py` - Split news archive into individual files
- `extract_security.py` - Parse CVE entries from security page
- `convert_to_markdown.py` - Convert HTML to markdown (lossy, not priority)
- `migrate_rss.py` - Convert awk/sed RSS to Hugo templates
