.PHONY: install build lint typecheck test check

install:
	pip install -r requirements.txt

# "Build": byte-compile every Python file (catches syntax errors) and import the app.
build:
	python -m compileall -q src tests wsgi.py passenger_wsgi.py
	DATABASE_URL=sqlite:///:memory: python -c "from src.main import app; print('App import OK:', app.name)"

lint:
	python -m pyflakes src tests

typecheck:
	python -m mypy src

test:
	python -m pytest

check: build typecheck test
