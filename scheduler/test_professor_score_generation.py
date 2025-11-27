from unittest import TestCase
from professor_score_generation import analyze_review


class Test(TestCase):
    def test_positive_review(self):
        result = analyze_review("This professor was the best")
        self.assertEqual(result, "positive")
    def test_negative_review(self):
        result = analyze_review("This professor was the worst")
        self.assertEqual(result, "negative")
    def test_empty_review(self):
        self.assertRaises(ValueError, analyze_review, "")
