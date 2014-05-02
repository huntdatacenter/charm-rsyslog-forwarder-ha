#!/usr/bin/make
PYTHON := /usr/bin/env python

build: sync-charm-helpers lint

lint:
	@flake8 --exclude hooks/charmhelpers --ignore=E125 hooks

test:
	#@pip install -r test_requirements.txt
	@PYTHONPATH=$(PYTHON_PATH):hooks/ nosetests --nologcapture tests 

bin/charm_helpers_sync.py:
	@bzr cat lp:charm-helpers/tools/charm_helpers_sync/charm_helpers_sync.py > bin/charm_helpers_sync.py

sync-charm-helpers: bin/charm_helpers_sync.py
	@$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml

deploy:
	@echo Deploying charm-rsyslog-forwarder-ha template.
	@juju deploy --repository=../.. local:trusty/rsyslog-forwarder-ha
	@echo See the README for explorations after deploying.
