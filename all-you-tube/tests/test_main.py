from gaba import main
import mock
from unittest import TestCase


class Test(TestCase):

    def test_get_input(self):
        with mock.patch('gaba.main.input', return_value='valid input'):
            self.assertEqual(main.get_input(), 'valid input')

    @mock.patch('gaba.main.print')
    @mock.patch('gaba.main.get_input', return_value="Good day!")
    def test_main_print(self, mock_get_input, mock_print):
        greeting = "Good day!"
        main.main()

        calls = [mock.call(greeting)]
        self.assertEqual(mock_print.mock_calls, calls)
