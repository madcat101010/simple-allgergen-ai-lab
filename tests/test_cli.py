"""
Unit tests for Agent CLI Entrypoint (src/cli.py)
"""

import sys
import unittest
from unittest.mock import patch
from src.cli import main


class TestAgentCLI(unittest.TestCase):
    def test_cli_menu_command(self):
        test_args = ["cli.py", "menu"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

    def test_cli_chat_command(self):
        test_args = ["cli.py", "chat", "Is a Big Mac safe?", "--allergies", "Gluten"]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
