# Shortcuts for developers (macOS / Linux). Game designers can just use
# play.command, play.bat or ./play.sh instead.
PYTHON ?= python3

.PHONY: play check catalogue test docs census clean help

help:
	@echo "make play       start the game (MODE=easy to choose a mode)"
	@echo "make check      check that Python, numpy and tkinter are ready"
	@echo "make catalogue  list every piece by difficulty class"
	@echo "make test       run all automatic tests"
	@echo "make docs       regenerate docs/api.md and the Phase 1 census"
	@echo "make clean      remove Python cache folders"

play:
	$(PYTHON) play.py $(if $(MODE),--mode $(MODE))

check:
	$(PYTHON) play.py --check

catalogue:
	$(PYTHON) play.py --catalogue

test:
	$(PYTHON) -B -m unittest discover -s tests -v

docs:
	$(PYTHON) -B tools/make_api_docs.py
	$(PYTHON) -B tools/shape_census.py --write

census:
	$(PYTHON) -B tools/shape_census.py

clean:
	find src tests tools examples -name __pycache__ -type d -prune -exec rm -rf {} +
