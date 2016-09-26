#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Jorge Niedbalski R. <jorge.niedbalski@canonical.com>'


import amulet
import unittest


class RsyslogForwarder(unittest.TestCase):

    def setUp(self):
        pass

    def test_deployment_single(self):
        """Test a rsyslog-forwarder-ha deployment"""
        self.deployment = amulet.Deployment(series="xenial",
                                            sentries=False)

        self.deployment.add("cs:trusty/rsyslog")
        self.deployment.add("cs:~bigdata-dev/xenial/rsyslog-forwarder-ha")
        self.deployment.add("cs:xenial/ubuntu")

        self.deployment.relate("rsyslog-forwarder-ha:syslog",
                               "rsyslog:aggregator")

        self.deployment.relate("ubuntu:juju-info",
                               "rsyslog-forwarder-ha:juju-info")

        self.deployment.setup(timeout=600)
        self.deployment.sentry.wait(timeout=600)


if __name__ == "__main__":
    unittest.main()
