"""Branch and state checks, separate from the Unit 4 acceptance evaluations."""
import unittest
from unittest.mock import Mock, patch

import agent
from utils.data_loader import get_example_wardrobe, load_listings


class AgentTests(unittest.TestCase):
    def test_query_parser(self):
        cases = [
            ('vintage graphic tee under $30, size M', 'vintage graphic tee', 'M', 30.0),
            ('90s track jacket in size M', '90s track jacket', 'M', None),
            ('platform sneakers size 8.5', 'platform sneakers', '8.5', None),
            ('jeans size W30 L30 under $38.50', 'jeans', 'W30 L30', 38.5),
            ('a tee size S/M up to $20', 'tee', 'S/M', 20.0),
            ('looking for a vintage tee', 'vintage tee', None, None),
            ('hat size One Size', 'hat', 'One Size', None),
        ]
        for query, description, size, price in cases:
            with self.subTest(query=query):
                self.assertEqual(agent.parse_query(query), dict(description=description, size=size, max_price=price))

    def test_state_identity_and_tool_order(self):
        item = load_listings()[5]
        wardrobe = get_example_wardrobe()
        calls = Mock()
        with patch.object(agent.mcp_client, 'call_tool', return_value=[item]) as search, patch.object(agent, 'suggest_outfit', return_value='Outfit') as outfit, patch.object(agent, 'create_fit_card', return_value='Caption') as card:
            for name, tool in [('search', search), ('outfit', outfit), ('card', card)]:
                calls.attach_mock(tool, name)
            session = agent.run_agent('graphic tee under $30', wardrobe)
        self.assertEqual([c[0] for c in calls.mock_calls], ['search', 'outfit', 'card'])
        search.assert_called_once_with('search_listings', {'description': 'graphic tee', 'size': None, 'max_price': 30.0})
        self.assertIs(session['selected_item'], session['search_results'][0])
        self.assertIs(outfit.call_args.args[0], session['selected_item'])
        self.assertIs(outfit.call_args.args[1], session['wardrobe'])
        self.assertIs(card.call_args.args[0], session['outfit_suggestion'])
        self.assertIs(card.call_args.args[1], session['selected_item'])
        self.assertEqual(session['fit_card'], 'Caption')
        self.assertIsNone(session['error'])

    def test_impossible_query_never_calls_model_tools(self):
        with patch.object(agent, 'suggest_outfit') as outfit, patch.object(agent, 'create_fit_card') as card:
            session = agent.run_agent('designer ballgown size XXS under $5', get_example_wardrobe())
        outfit.assert_not_called()
        card.assert_not_called()
        self.assertEqual(session['search_results'], [])
        for key in ['selected_item', 'outfit_suggestion', 'fit_card']:
            self.assertIsNone(session[key])
        self.assertIn('broader keywords', session['error'])
        self.assertIn('different size', session['error'])
        self.assertIn('higher price limit', session['error'])

    def test_iteration_guard_runs_before_each_step(self):
        with patch.object(agent.config, 'MAX_ITERATIONS', 1), patch.object(agent.mcp_client, 'call_tool', return_value=[load_listings()[0]]), patch.object(agent, 'suggest_outfit') as outfit:
            with self.assertRaisesRegex(RuntimeError, 'MAX_ITERATIONS'):
                agent.run_agent('jeans', {'items': []})
            outfit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
