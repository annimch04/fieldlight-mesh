# Local dev / parity with .github/workflows/ci.yml
# Usage: make install && make check && make go-probe

PYTHON3 ?= python3
VENV    ?= .venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
PYCACHE ?= $(VENV)/pycache

.PHONY: venv install check go-probe ci-local help

help:
	@echo "Targets: venv install check go-probe ci-local help"
	@echo "  install   - create .venv and pip install -r requirements.txt"
	@echo "  check     - compileall + sil_mesh --help (needs install)"
	@echo "  go-probe  - go build discovery/libp2p_peer_probe"
	@echo "  ci-local  - check + go-probe"

venv:
	$(PYTHON3) -m venv $(VENV)

install: venv
	$(PIP) install -U pip
	$(PIP) install -e '.[discovery,dev]'

check:
	@test -x $(PY) || (echo >&2 "Run: $(MAKE) install"; exit 1)
	PYTHONPYCACHEPREFIX=$(PYCACHE) $(PY) -m compileall fieldlight_mesh scripts -q
	$(PY) scripts/sil_mesh.py receive --help >/dev/null
	$(PY) scripts/sil_mesh.py send --help >/dev/null
	$(PY) scripts/sil_mesh.py discover --help >/dev/null
	$(PY) -m fieldlight_mesh --help >/dev/null
	$(PY) -m pytest -q

go-probe:
	cd discovery/libp2p_peer_probe && go build -v -o /dev/null .

ci-local: check go-probe
