"""Failure handling and opt-in tracing, without live model calls."""
import contextlib
import io
import unittest
from unittest.mock import patch

import agent
from generate import ModelUnavailable
from utils.data_loader import load_listings


class FailureTests(unittest.TestCase):
    def test_model_failure_at_either_step_preserves_state_and_hides_raw_error(self):
        item = load_listings()[0]
        for failing_step in ['outfit', 'card']:
            with self.subTest(step=failing_step), patch.object(agent.mcp_client, 'call_tool', return_value=[item]), patch.object(agent, 'suggest_outfit', return_value='Advice') as outfit, patch.object(agent, 'create_fit_card', return_value='Caption') as card:
                (outfit if failing_step == 'outfit' else card).side_effect = ModelUnavailable('private provider detail')
                session = agent.run_agent('jeans', {'items': []})
                self.assertIn('Check GEMINI_API_KEY', session['error'])
                self.assertNotIn('private provider detail', session['error'])
                self.assertIs(session['selected_item'], item)
                self.assertIsNone(session['fit_card'])
                if failing_step == 'outfit':
                    card.assert_not_called()
                    self.assertIsNone(session['outfit_suggestion'])
                else:
                    self.assertEqual(session['outfit_suggestion'], 'Advice')

    def test_trace_is_opt_in_and_resets_for_each_run(self):
        with patch.object(agent.mcp_client, 'call_tool', return_value=[]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                agent.run_agent('nothing', {'items': []}, use_trace=True)
            self.assertIn('[1] parse_query', output.getvalue())
            self.assertIn('search_listings (via MCP)', output.getvalue())
            self.assertIn('branch: empty search', output.getvalue())
            self.assertNotIn('] suggest_outfit', output.getvalue())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                agent.run_agent('nothing', {'items': []})
            self.assertEqual(output.getvalue(), '')
            self.assertEqual(agent.trace.get_trace(), '')

    def test_full_trace_includes_all_tools_and_empty_wardrobe(self):
        with patch.object(agent.mcp_client, 'call_tool', return_value=[load_listings()[0]]), patch.object(agent, 'suggest_outfit', return_value='General advice') as outfit, patch.object(agent, 'create_fit_card', return_value='Caption'), contextlib.redirect_stdout(io.StringIO()):
            result = agent.run_agent('jeans', {'items': []}, use_trace=True)
        self.assertEqual(outfit.call_args.kwargs['wardrobe'], {'items': []})
        self.assertIsNone(result['error'])
        self.assertIn('[4] suggest_outfit', agent.trace.get_trace())
        self.assertIn('[5] create_fit_card', agent.trace.get_trace())
        self.assertIn('wardrobe items: 0', agent.trace.get_trace())

    def test_model_failure_is_traced(self):
        with patch.object(agent.mcp_client, 'call_tool', return_value=[load_listings()[0]]), patch.object(agent, 'suggest_outfit', side_effect=ModelUnavailable('offline')), contextlib.redirect_stdout(io.StringIO()):
            agent.run_agent('jeans', {'items': []}, use_trace=True)
        self.assertIn('model unavailable; stopping', agent.trace.get_trace())
        self.assertNotIn('] create_fit_card', agent.trace.get_trace())


if __name__ == '__main__':
    unittest.main()
