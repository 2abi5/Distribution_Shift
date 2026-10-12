# Distribution shift in agricultural machine learning — systematic review
# Pipeline: extraction CSVs -> review/scripts/synthesis.py -> analysis/results.json + figures
#           -> manuscript/build.py (renders every number from results.json) -> output/*.docx, *.pdf
# S is the path to the research-pro scripts:  make check S=/path/to/abinash_research/skills/research-pro/scripts
S       ?= $(abspath ../../abinash_research/skills/research-pro/scripts)
VERSION ?= v1.1

.PHONY: all synthesis paper check prose cites tokens score archive

all: synthesis paper

synthesis:
	cd review && python3 scripts/synthesis.py

paper:
	cd manuscript && python3 build.py --version $(VERSION)

check: prose cites tokens

prose: paper
	cd manuscript && python3 -c "s=open('build/review_rendered.md').read().split('# References {-}')[0]; \
	  open('build/body.md','w').write('\n'.join(l for l in s.split('\n') if not l.startswith(('|', ': Table', '!['))))" \
	  && python3 -c "import pypandoc; pypandoc.convert_file('build/body.md', 'latex', outputfile='build/body.tex')" \
	  && python3 $(S)/prose_metrics.py build/body.tex --no-strict

cites:
	cd manuscript && mkdir -p build && cat refs.bib generated/included.bib > build/all_refs.bib \
	  && python3 $(S)/verify_citations.py build/all_refs.bib --report citation_report.md --resolved citation_resolutions.json --no-strict $(if $(MAILTO),--mailto $(MAILTO))

tokens: paper
	@grep -nE '\[(NEEDS SOURCE|TBD|NEEDS EXPERIMENT|AUTHOR DECISION|VERIFY)' manuscript/build/review_rendered.md manuscript/build/title_page_rendered.md \
	  || echo "no gate tokens"

score:
	python3 $(S)/score_readiness.py readiness.json --venue technology-in-society --registry venue_registry.json

# Data and code archive for Zenodo/OSF: everything except full texts (copyright), build directories and outputs.
# The zip root is named $(ARCHIVE_ROOT) (a temporary symlink to this directory, which zip follows).
ARCHIVE_ROOT ?= distribution_shift_review
ARCHIVE      := $(ARCHIVE_ROOT)_data_and_code_$(VERSION).zip
archive:
	rm -f ../$(ARCHIVE)
	cd .. && ln -sfn $(notdir $(CURDIR)) $(ARCHIVE_ROOT) && zip -qr $(ARCHIVE) $(ARCHIVE_ROOT) \
	  -x '$(ARCHIVE_ROOT)/review/fulltext/pdf/*' '$(ARCHIVE_ROOT)/review/fulltext/txt/*' '$(ARCHIVE_ROOT)/review/fulltext/html/*' \
	     '$(ARCHIVE_ROOT)/review/fulltext/chrome-profile*' '$(ARCHIVE_ROOT)/review/fulltext/retry/*.pdf' '$(ARCHIVE_ROOT)/review/fulltext/retry/*.html' \
	     '$(ARCHIVE_ROOT)/manuscript/build/*' '$(ARCHIVE_ROOT)/output/*' '*/__pycache__/*' '*.DS_Store' '*.out'; rm -f $(ARCHIVE_ROOT)
	@unzip -l ../$(ARCHIVE) | tail -1 && ls -la ../$(ARCHIVE)
