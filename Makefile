#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = aug-11-agents-hackathon
PYTHON_VERSION = 3.10
PYTHON_INTERPRETER = python3

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install uv
.PHONY: install_uv
install_uv:
	$(PYTHON_INTERPRETER) -m pip install --upgrade pip
	$(PYTHON_INTERPRETER) -m pip install uv

## Install Python Dependencies
.PHONY: requirements
requirements: install_uv
	uv pip install -r requirements.txt

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 backend
	isort --check --diff --profile black backend
	black --check --config pyproject.toml backend

## Format source code with black
.PHONY: format
format:
	black --config pyproject.toml backend

## Set up python interpreter environment
.PHONY: create_environment
create_environment:
	@bash -c "if [ ! -z `which virtualenvwrapper.sh` ]; then source `which virtualenvwrapper.sh`; mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER); else mkvirtualenv.bat $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER); fi"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"

## Create Virtual Environment
.PHONY: venv
venv:
	$(PYTHON_INTERPRETER) -m venv .venv

## Install dependencies in the virtual environment
.PHONY: install
install: venv
	. .venv/bin/activate && $(MAKE) install_uv && $(MAKE) requirements

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Make Dataset
.PHONY: data
data: requirements
	$(PYTHON_INTERPRETER) backend/data/make_dataset.py

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)