"""Tool contract checks without model requests; separate from acceptance evals."""
import unittest
from unittest.mock import patch

import tools
from generate import ModelUnavailable
from utils.data_loader import load_listings


class SearchTests(unittest.TestCase):
    def test_size_boundaries(self):
        for wanted, listed, expected in [
            ('M', 'S/M', True), ('l', 'L/XL', True), ('L', 'XL', False),
            ('S', 'US 9', False), ('8', 'US 8.5', False), ('8.5', 'US 8.5', True),
            ('W30', 'W30 L30', True), ('W30 L32', 'W30 L30', False),
            ('XL', 'XL (oversized)', True), ('One Size', 'One Size / Oversized', True),
            ('M', 'One Size', False), (' S/M ', 'M/L', True),
        ]:
            with self.subTest(wanted=wanted, listed=listed):
                self.assertEqual(tools._size_matches(wanted, listed), expected)

    def test_filters_and_empty_results(self):
        found = tools.search_listings('graphic tee', size='m', max_price=18.0)
        self.assertIn('lst_002', [item['id'] for item in found])
        self.assertTrue(all(item['price'] <= 18 for item in found))
        self.assertEqual(tools.search_listings('graphic tee', size='XXS', max_price=5), [])
        self.assertEqual(tools.search_listings('   !!!'), [])
        self.assertEqual(tools.search_listings('zzzznomatch'), [])
        self.assertEqual(tools.search_listings('tee', max_price=0), [])

    def test_ranking_ties_limit_and_original_records(self):
        base = load_listings()[0]
        records = [dict(base, id=str(i), title=title, description='', category='',
                        style_tags=[]) for i, title in enumerate(['tee', 'graphic tee', 'graphic tee'])]
        with patch.object(tools, 'load_listings', return_value=records), patch.object(tools.config, 'SEARCH_RESULT_LIMIT', 2):
            result = tools.search_listings('graphic graphic tee')
        self.assertEqual([item['id'] for item in result], ['1', '2'])
        self.assertIs(result[0], records[1])


class ModelToolTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[5]  # No brand.

    def test_empty_outfit_avoids_model(self):
        with patch.object(tools, 'generate') as model:
            for outfit in ['', ' \n\t']:
                self.assertEqual(tools.create_fit_card(outfit, self.item),
                                 'Cannot create a fit card without an outfit suggestion.')
            model.assert_not_called()

    def test_blank_model_responses(self):
        with patch.object(tools, 'generate', return_value=' \n'):
            self.assertEqual(tools.suggest_outfit(self.item, {'items': []}),
                             'No outfit suggestion was generated. Please try again.')
            self.assertEqual(tools.create_fit_card('jeans', self.item),
                             'No fit card was generated. Please try again.')

    def test_empty_wardrobe_prompt_and_response(self):
        with patch.object(tools, 'generate', return_value=' General advice. ') as model:
            self.assertEqual(tools.suggest_outfit(self.item, {'items': []}), 'General advice.')
            prompt = model.call_args.args[0]
            self.assertIn('no wardrobe items were supplied', prompt)
            self.assertIn('"items": []', prompt)
            self.assertIn(self.item['id'], prompt)

    def test_service_failures_remain_distinct(self):
        with patch.object(tools, 'generate', side_effect=ModelUnavailable('unavailable')):
            with self.assertRaises(ModelUnavailable):
                tools.suggest_outfit(self.item, {'items': []})
            with self.assertRaises(ModelUnavailable):
                tools.create_fit_card('jeans', self.item)


if __name__ == '__main__':
    unittest.main()
