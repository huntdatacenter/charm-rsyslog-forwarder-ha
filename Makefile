#!/usr/bin/make
PYTHON := /usr/bin/env python

build: sync-charm-helpers lint

lint:
	@flake8 --exclude hooks/charmhelpers --ignore=E125,F401 hooks

test:
	@dpkg -s python-apt > /dev/null || sudo apt-get install python-apt
	@sudo pip install -r test_requirements.txt
	@PYTHONPATH=$(PYTHON_PATH):hooks/ nosetests --nologcapture tests/unit

bin/charm_helpers_sync.py:
	@bzr cat lp:charm-helpers/tools/charm_helpers_sync/charm_helpers_sync.py > bin/charm_helpers_sync.py

sync-charm-helpers: bin/charm_helpers_sync.py
	@$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml

deploy:
	@echo Deploying charm-rsyslog-forwarder-ha template.
	@juju deploy --repository=../.. local:trusty/rsyslog-forwarder-ha
	@echo See the README for explorations after deploying.
