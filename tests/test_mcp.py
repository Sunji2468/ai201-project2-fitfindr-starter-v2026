"""Real stdio checks for the search tool's protocol boundary; no model calls."""
import unittest

from mcp_client import call_tool, MCPError
from tools import search_listings


class MCPTests(unittest.TestCase):
    def test_direct_and_mcp_search_results_match(self):
        cases = [
            {'description': 'vintage graphic tee'},
            {'description': 'graphic tee', 'size': 'M', 'max_price': 18.0},
            {'description': 'sneakers', 'size': '8', 'max_price': None},
            {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0},
            {'description': ''},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = call_tool('search_listings', arguments)
                self.assertIsInstance(result, list)
                self.assertEqual(result, search_listings(**arguments))

    def test_required_description_is_enforced(self):
        with self.assertRaises(MCPError):
            call_tool('search_listings', {'max_price': 30.0})


if __name__ == '__main__':
    unittest.main()
