#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Define utility functions to support rsyslog-forwarder-ha charm."""

import os
import sys
from subprocess import CalledProcessError

from charmhelpers import fetch
from charmhelpers.core import hookenv

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    try:
        fetch.apt_install("python-jinja2")
        from jinja2 import Environment, FileSystemLoader
    except (ImportError, CalledProcessError):
        pass


def __die(message):
    hookenv.log(message, hookenv.ERROR)
    sys.exit(1)


def get_template_dir():
    return os.path.join(hookenv.charm_dir(), "templates")


def get_template(name):
    template_env = Environment(loader=FileSystemLoader(get_template_dir()))
    return template_env.get_template(name + ".template")
