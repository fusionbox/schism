from mock import MagicMock, patch, call
import unittest

from schism.utils import log


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('sys.stderr')
        self.mock_stderr = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_log_without_function_args_logs_exact_message(self):
        log('Starborks')
        self.mock_stderr.write.assert_called_with('Starborks')

    def test_log_with_function_args_logs_extra_messages_and_runs_function(self):
        test_func = MagicMock()

        log('Running test function', test_func, 1, 'arst', foo='bar')

        self.assertEqual(
            self.mock_stderr.write.mock_calls,
            [call('Running test function'), call('...'), call('done\n')],
        )
        test_func.assert_called_with(1, 'arst', foo='bar')
