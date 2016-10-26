#!/usr/bin/env python3

import amulet
import unittest


class RsyslogForwarder(unittest.TestCase):
    """
    Trivial deployment test for rsyslog-forwarder-ha.
    """
    @classmethod
    def setUpClass(cls):
        cls.d = amulet.Deployment(series='xenial')

        cls.d.add("rsyslog", "cs:~bigdata-dev/xenial/rsyslog")
        cls.d.add("rsyslog-forwarder-ha", "cs:~bigdata-dev/xenial/rsyslog-forwarder-ha")
        cls.d.add("syslog-source", "cs:xenial/ubuntu")

        cls.d.relate("rsyslog-forwarder-ha:syslog", "rsyslog:aggregator")
        cls.d.relate("syslog-source:juju-info", "rsyslog-forwarder-ha:juju-info")

        cls.d.setup(timeout=600)
        cls.d.sentry.wait(timeout=600)
        cls.unit = cls.d.sentry['syslog-source'][0]

    def test_deploy(self):
        """
        Simple test to make sure the rsyslogd process is running.
        """
        output, retcode = self.unit.run("pgrep -a rsyslogd")
        assert 'rsyslogd' in output, "rsyslog daemon is not running"


if __name__ == "__main__":
    unittest.main()
