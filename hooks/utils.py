#!/usr/bin/python3
# -*- coding: utf-8 -*-

from subprocess import CalledProcessError

from charmhelpers.core import hookenv
from charmhelpers import fetch

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    try:
        fetch.apt_install("python-jinja2")
        from jinja2 import Environment, FileSystemLoader
    except (ImportError, CalledProcessError):
        pass

import os
import sys


def __die(message):
    hookenv.log(message, hookenv.ERROR)
    sys.exit(1)


def get_template_dir():
    return os.path.join(hookenv.charm_dir(), 'templates')


def get_template(name):
    template_env = Environment(loader=FileSystemLoader(get_template_dir()))
    return template_env.get_template(name + '.template')
