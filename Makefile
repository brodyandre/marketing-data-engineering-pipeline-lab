PYTHON ?= python

.PHONY: up down install test extract transform quality load pipeline clean

up:
	docker compose up -d

down:
	docker compose down

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

test:
	pytest

extract:
	$(PYTHON) -m src.extract

transform:
	$(PYTHON) -m src.transform

quality:
	$(PYTHON) -m src.quality

load:
	$(PYTHON) -m src.load

pipeline:
	$(PYTHON) -m src.pipeline

clean:
	$(PYTHON) -c "import shutil; from pathlib import Path; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__')]; [shutil.rmtree(Path(n), ignore_errors=True) for n in ['.pytest_cache', '.mypy_cache', 'htmlcov'] if Path(n).exists()]; [p.unlink() for p in Path('.').rglob('*.pyc') if p.is_file()]; [p.unlink() for p in Path('data/processed').glob('*.csv') if p.is_file()]"
