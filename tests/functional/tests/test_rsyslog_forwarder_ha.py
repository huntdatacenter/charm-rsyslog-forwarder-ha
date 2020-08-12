#!/usr/bin/python3

"""Encapsulate rsyslog-forwarder-ha testing."""
import logging
import time
import unittest

import zaza.model as model


LOG_SEND_TIMEOUT = 300


class BaseRsyslogForwarderHaTest(unittest.TestCase):
    """Base for rsyslog-forwarder-ha charm tests."""

    @classmethod
    def setUpClass(cls):
        """Set up tests."""
        super(BaseRsyslogForwarderHaTest, cls).setUpClass()
        cls.model_name = model.get_juju_model()
        cls.application_name = "rsyslog"
        cls.lead_unit_name = model.get_lead_unit_name(
            cls.application_name, model_name=cls.model_name
        )
        cls.source_application_name = "rsyslog-forwarder-ha"
        cls.source_unit_name = model.get_lead_unit_name(
            cls.source_application_name, model_name=cls.model_name
        )


class CharmOperationTest(BaseRsyslogForwarderHaTest):
    """Verify operations."""

    def test_01_rsyslog_receiving_data(self):
        """Verify if the API is ready.

        Curl the api endpoint.
        We'll retry until the LOG_SEND_TIMEOUT
        """
        logger_cmd = "logger 'functional-testing'"
        response = model.run_on_unit(self.source_unit_name, logger_cmd)
        if response["Code"] != "0":
            self.fail(
                "Failed to run logger on rsyslog source host. {}".format(response)
            )

        timeout = time.time() + LOG_SEND_TIMEOUT
        while time.time() < timeout:
            grep_cmd = "grep functional-testing /var/log/syslog"
            response = model.run_on_unit(self.lead_unit_name, grep_cmd)
            if response["Code"] == "0":
                return
            logging.warning(
                "Failed to find functional-testing in rsyslog destination"
                "Retrying in 5s."
            )
            time.sleep(5)

        # we didn't get rc=0 in the allowed time, fail the test
        self.fail(
            "rsyslog didn't receive functional-testing log entry from source. "
            "Stdout: {stdout}, Stderr: {stderr}, RC: {retcode}".format(
                stdout=response["Stdout"],
                stderr=response["Stderr"],
                retcode=response["Code"],
            )
        )
