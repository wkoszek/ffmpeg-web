# FFmpeg Website - Hugo Version

This directory contains the Hugo-based version of the FFmpeg website, migrated from the custom Makefile-based system.

## Quick Start

```bash
# Build the site
make

# Start development server with live reload
make dev

# Verify output matches original
make verify
```

## Requirements

- Hugo v0.140.2+ (extended version)
- Python 3.11+ with lxml (for verification)

## Directory Structure

```
hugo-site/
├── Makefile              # Build targets
├── hugo.toml            # Hugo configuration
├── content/             # Page content (14 pages)
│   ├── _index.md       # Homepage
│   ├── about.md        # About page
│   └── ...
├── themes/ffmpeg/       # Custom theme
│   └── layouts/
│       ├── _default/
│       │   ├── baseof.html   # Base template
│       │   └── single.html   # Page template
│       └── index.html         # Homepage template
├── static/              # Static assets (CSS, JS, fonts, images)
└── public/              # Generated site (after build)
```

## Makefile Targets

- `make` or `make build` - Build the site to public/
- `make dev` - Start Hugo development server
- `make clean` - Remove generated files
- `make rebuild` - Clean and build from scratch
- `make verify` - Verify output matches original site
- `make verify-page PAGE=<name>` - Verify single page
- `make help` - Show all available targets

## Content Format

Content files use Hugo frontmatter (TOML) + preserved HTML:

```markdown
+++
title = "About FFmpeg"
slug = "about"
type = "page"

[checksums]
content = "sha256..."
title = "sha256..."
js = "sha256..."
+++

<p class="with-icon">
  <!-- Original HTML preserved here -->
</p>
```

## Configuration Notes

Key Hugo config settings in `hugo.toml`:

- `uglyURLs = true` - Generates `about.html` instead of `about/index.html`
- `unsafe = true` - Allows raw HTML in markdown (required for preserved content)
- `disableKinds = ['taxonomy', 'term', 'RSS']` - Disables unused Hugo features

## Migration Details

See `../MIGRATION_REPORT.md` for complete migration documentation.

## Differences from Original

The Hugo-generated HTML differs from the original only in:

1. **Whitespace** - Some blank lines between paragraphs removed
2. **IE9 comments** - Conditional comments stripped (IE9 obsolete since 2016)

**Zero functional differences** - All content, structure, and behavior identical.

## Development Workflow

1. **Edit content** - Modify files in `content/`
2. **Edit templates** - Modify files in `themes/ffmpeg/layouts/`
3. **Test locally** - Run `make dev` and view at http://localhost:1313
4. **Verify** - Run `make verify` to check against original
5. **Build** - Run `make` to generate production files

## Deployment

Build output is in `public/` directory. Deploy these files to web server:

```bash
make rebuild
rsync -av public/ user@server:/var/www/ffmpeg.org/
```

Or use Hugo's built-in deployment (configure in `hugo.toml`).

## RSS Feed

**Note:** RSS feed generation not yet migrated. Current site still uses awk/sed from original Makefile. See `../Makefile` lines 39-60 for RSS generation logic.

## Troubleshooting

**Build fails:**
```bash
# Check Hugo version
hugo version  # Should be v0.140.2+

# Check Hugo binary location
which hugo

# Clean and rebuild
make rebuild
```

**Verification fails with "different":**
- Expected - only whitespace and IE9 comment differences
- Review diff: `diff -u ../htdocs/about.html public/about.html | less`
- See `../MIGRATION_REPORT.md` for explanation

**Assets not loading:**
- Check `static/` directory has CSS, JS, fonts, images
- Rebuild: `make rebuild`

## Original System

For comparison, the original Makefile-based system:

```bash
cd ..
make  # Builds to ../htdocs/
```

Both systems can coexist during testing.
