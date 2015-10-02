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
        self.deployment = amulet.Deployment(series="precise",
                                            sentries=False)

        self.deployment.add("rsyslog-master", charm="rsyslog")
        self.deployment.add("rsyslog-slave", charm="rsyslog")
        self.deployment.add("rsyslog-forwarder-ha")
        self.deployment.add("postgresql")

        self.deployment.relate("rsyslog-forwarder-ha:syslog",
                               "rsyslog-master:aggregator")

        self.deployment.relate("rsyslog-forwarder-ha:syslog",
                               "rsyslog-slave:aggregator")

        self.deployment._relate("postgresql", "rsyslog-forwarder-ha")

        self.deployment.expose("rsyslog-master")
        self.deployment.expose("rsyslog-slave")

        self.deployment.setup(timeout=600)
        self.deployment.sentry.wait(timeout=600)


if __name__ == "__main__":
    unittest.main()
