# ffmpeg.org HTML generation from source files

SRCS = about bugreports consulting contact donations documentation download \
       olddownload index legal shame security spi archive

HTML_TARGETS  = $(addsuffix .html,$(addprefix htdocs/,$(SRCS)))

RSS_FILENAME = main.rss
RSS_TARGET = htdocs/$(RSS_FILENAME)

CSS_SRCS = src/less/style.less
CSS_TARGET = htdocs/css/style.min.css
LESS_TARGET = htdocs/style.less
LESSC_OPTIONS := --clean-css

BOWER_PACKAGES = bower.json
BOWER_COMPONENTS = htdocs/components

ifdef DEV
SUFFIX = dev
TARGETS = $(BOWER_COMPONENTS) $(LESS_TARGET) $(HTML_TARGETS) $(RSS_TARGET)
else
SUFFIX = prod
TARGETS = $(HTML_TARGETS) $(CSS_TARGET) $(RSS_TARGET)
endif

DEPS = src/template_head1 src/template_head2 src/template_head3 src/template_head_$(SUFFIX) \
       src/template_footer1 src/template_footer2 src/template_footer_$(SUFFIX)

all: htdocs

htdocs: $(TARGETS)

htdocs/%.html: src/% src/%_title src/%_js $(DEPS)
	cat src/template_head1 $<_title src/template_head_$(SUFFIX) \
	src/template_head2 $<_title src/template_head3 $< \
	src/template_footer1 src/template_footer_$(SUFFIX) $<_js src/template_footer2 > $@

$(RSS_TARGET): htdocs/index.html
	echo '<?xml version="1.0" encoding="UTF-8" ?>' > $@
	echo '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">' >> $@
	echo '<channel>' >> $@
	echo '    <title>FFmpeg RSS</title>' >> $@
	echo '    <link>http://ffmpeg.org</link>' >> $@
	echo '    <description>FFmpeg RSS</description>' >> $@
	echo '    <atom:link href="http://ffmpeg.org/main.rss" rel="self" type="application/rss+xml" />' >> $@
	awk '/<h3 *id=".*" *> *.*20.., *.*<\/h3>/ { p = 1 } /<h1>Older entries are in the .*news archive/ { p = 0 } p' $< \
        | sed 'sX<h3 *id="\(.*\)" *> *\(.*20..\), *\(.*\)</h3>X\
        ]]></content:encoded>\
    </item>\
    <item>\
        <title>\2, \3</title>\
        <link>http://ffmpeg.org/index.html#\1</link>\
        <guid>http://ffmpeg.org/index.html#\1</guid>\
        <content:encoded><![CDATA[X' \
	| awk 'NR > 3' >> $@
	echo '        ]]></content:encoded>' >> $@
	echo '    </item>' >> $@
	echo '</channel>' >> $@
	echo '</rss>' >> $@

$(BOWER_COMPONENTS): $(BOWER_PACKAGES)
	bower install
	cp -r $(BOWER_COMPONENTS)/font-awesome/fonts htdocs/
	cp $(BOWER_COMPONENTS)/font-awesome/css/font-awesome.min.css htdocs/css/
	cp $(BOWER_COMPONENTS)/bootstrap/dist/css/bootstrap.min.css htdocs/css/
	cp $(BOWER_COMPONENTS)/bootstrap/dist/js/bootstrap.min.js htdocs/js/
	cp $(BOWER_COMPONENTS)/jquery/dist/jquery.min.js htdocs/js/

$(CSS_TARGET): $(CSS_SRCS)
	lessc $(LESSC_OPTIONS) $(CSS_SRCS) > $@

$(LESS_TARGET): $(CSS_SRCS)
	ln -sf $(CSS_SRCS) $@

clean:
	$(RM) -r $(TARGETS)

# Generate clean Markdown-based Hugo site in tmp/clean/
clean-md: tmp/clean/.done

tmp/clean/.done:
	@echo "Creating clean Markdown-based site in tmp/clean/..."
	@# Create directory structure
	mkdir -p tmp/clean
	@# Copy Hugo configuration and theme
	cp hugo-site/hugo.toml tmp/clean/
	cp hugo-site/Makefile tmp/clean/
	cp -r hugo-site/themes tmp/clean/
	@if [ -d hugo-site/static ]; then cp -r hugo-site/static tmp/clean/; fi
	@if [ -d hugo-site/archetypes ]; then cp -r hugo-site/archetypes tmp/clean/; fi
	@# Generate Markdown content from source files
	@echo "Converting HTML content to Markdown..."
	python3 scripts/extract_content.py all tmp/clean/content --markdown
	@# Copy static assets from htdocs (if they exist)
	@if [ -d htdocs/css ]; then mkdir -p tmp/clean/static/css && cp -r htdocs/css/* tmp/clean/static/css/; fi
	@if [ -d htdocs/js ]; then mkdir -p tmp/clean/static/js && cp -r htdocs/js/* tmp/clean/static/js/; fi
	@if [ -d htdocs/img ]; then mkdir -p tmp/clean/static/img && cp -r htdocs/img/* tmp/clean/static/img/; fi
	@if [ -d htdocs/fonts ]; then mkdir -p tmp/clean/static/fonts && cp -r htdocs/fonts/* tmp/clean/static/fonts/; fi
	@touch tmp/clean/.done
	@echo ""
	@echo "✓ Clean Markdown site created in tmp/clean/"
	@echo "  - Hugo templates: tmp/clean/themes/"
	@echo "  - Markdown content: tmp/clean/content/"
	@echo "  - Build with: cd tmp/clean && hugo"

clean-all: clean
	$(RM) -r tmp/clean

.PHONY: all clean clean-md clean-all
