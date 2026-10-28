import unittest
from decimal import Decimal

from estimate import NOTICE, estimate_cost


class EstimateCostTests(unittest.TestCase):
    def setUp(self):
        self.usage = {"input_tokens": 100_000, "cached_input_tokens": 40_000, "output_tokens": 10_000}
        self.rates = {"input": 1.5, "cached_input": 0.25, "output": 6.0}

    def test_hypothetical_estimate_splits_cached_input_once(self):
        result = estimate_cost(self.usage, self.rates)
        self.assertEqual(result["estimated_cost_usd"], "0.16")
        self.assertEqual(result["usage"]["uncached_input_tokens"], 60_000)
        self.assertIn("HYPOTHETICAL", result["notice"])

    def test_cache_count_must_be_subset_of_input(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            estimate_cost({**self.usage, "cached_input_tokens": 100_001}, self.rates)

    def test_counts_must_be_nonnegative_integers_not_booleans(self):
        for value in (-1, 1.0, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                estimate_cost({**self.usage, "output_tokens": value}, self.rates)

    def test_rates_must_be_finite_and_nonnegative(self):
        for value in (-0.1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                estimate_cost(self.usage, {**self.rates, "input": value})

    def test_zero_counts_and_rates_produce_zero(self):
        result = estimate_cost(
            {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0},
            {"input": Decimal("0"), "cached_input": Decimal("0"), "output": Decimal("0")},
        )
        self.assertEqual(result["estimated_cost_usd"], "0")


if __name__ == "__main__":
    unittest.main()
