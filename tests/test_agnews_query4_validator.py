"""Regression tests for answer-region validation, including contextual mentions."""

import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).resolve().parent.parent / "query_agnews/query4/validate.py"
SPEC = importlib.util.spec_from_file_location("agnews_query4_validator", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TestAgnewsQuery4Validator(unittest.TestCase):
    def test_accepts_correct_answer_surfaces(self):
        answers = [
            "Africa",
            "  AFRICA.  ",
            "**Africa**",
            '"Africa"',
            "The answer is Africa.",
            "Final answer: **Africa**.",
            "The region is Africa.",
            "Africa published the largest number of World articles in 2015.",
            "In 2015, Africa published the largest number of World-category articles, with 337 articles.",
            "The region with the largest number of World articles was Africa.",
            "Africa had the most World articles, followed by North America and Europe.",
            "Africa ranked first, ahead of North America.",
            "Africa, with 337 World articles.",
            "Africa (337 World-category articles).",
            "1. Africa\n2. North America\n3. Europe",
            "1) Africa (307 articles)\n2) North America (299 articles)",
            "The answer is Africa, not North America.",
            "Africa had the highest count; North America was the runner-up.",
            "Africa had the highest count.\nAfrica: 307\nSouth America: 301\nNorth America: 299",
            "| Region | World articles |\n|---|---|\n| North America | 299 |\n| Africa | 307 |\n| Asia | 295 |",
            "Africa and North America tied for the largest number of World articles.",
            "Africa ranked first, tied with North America.",
            "1. Africa and North America (tied)\n3. Europe",
            "1. North America\n1. Africa\n3. Europe",
            "| Region | World articles |\n|---|---|\n| Africa | 317 |\n| North America | 317 |",
            "In 2015, two regions tied for publishing the largest number of World-category articles: "
            "North America and Africa, each with 317 World articles. "
            "(For context: Europe had 315, South America had 315, and Asia had 304 World-category articles.)",
        ]
        for answer in answers:
            with self.subTest(answer=answer):
                self.assertTrue(MODULE.validate(answer)[0])

    def test_rejects_contextual_africa_mentions(self):
        answers = [
            # Real failure: the selected region is North America; Africa is third.
            "In 2015, North America published the largest number of articles in the World category, "
            "with 321 World articles (followed closely by South America at 320, Africa at 319, "
            "Europe at 316, and Asia at 299).",
            "North America",
            "The answer is North America, not Africa.",
            "Africa was the runner-up. North America had the most World articles.",
            "Africa did not publish the largest number of World articles.",
            "Africa isn't the winner.",
            "Not Africa.",
            "South Africa",
            "South Africa had the most World articles.",
            "The answer is Africa or North America.",
            "Africa had the most articles. North America had the highest count.",
            "Africa had the highest count, North America had the most World articles.",
            "It is unclear whether Africa had the most World articles.",
            "Perhaps Africa had the most World articles.",
            "Africa, with 319 World articles, was third.",
            "Africa had the second highest count.",
            "Africa published the third largest number of World articles.",
            "1. North America\n2. Africa\n3. Europe",
            "Africa did not rank first. Final answer: Africa.",
            "Africa: 319\nNorth America: 321\nSouth America: 320",
            "Africa: 317\nNorth America: 317\nAsia: 318",
            "North America and Asia tied for the largest number of World articles. Africa was third.",
            "Africa and North America tied for the second highest count.",
            "1. Africa or North America\n2. Europe",
            "Africa: 307\nAfrica: 300\nNorth America: 301",
            "I could not determine the answer.",
            "",
        ]
        for answer in answers:
            with self.subTest(answer=answer):
                self.assertFalse(MODULE.validate(answer)[0])

    def test_accepts_unnumbered_paraphrases_and_formats(self):
        answers = [
            "In 2015, Africa published more World articles than any other region.",
            "Africa published more articles than all other regions.",
            "Africa came out on top.",
            "Africa was number one.",
            "Africa ranked 1st.",
            "Africa finished first.",
            "Africa is the winner.",
            "Africa was jointly ranked first.",
            "Africa ranked first, tied with North America.",
            "- Africa: 321\n- North America: 319",
            "• Africa: 321\n• North America: 319",
            "Africa has the most World articles. North America has the highest population.",
            "Africa ranked first in 2015. North America ranked first in 2014.",
            "Africa had the most World articles. Asia had the most Sports articles.",
            "In 2015, the region that published the largest number of articles in the World category "
            "was **Africa**, with 337 World-category articles.",
            "Africa: 2014\nNorth America: 2013",
            "Africa: 2,014\nNorth America: 2,013",
            "Africa has the most articles, North America was second.",
            "Africa.\n| Region | Population |\n|---|---|\n| Africa | 100 |\n| Asia | 200 |",
            "The most World articles were published by Africa.",
        ]
        for answer in answers:
            with self.subTest(answer=answer):
                self.assertTrue(MODULE.validate(answer)[0])

    def test_rejects_misleading_relations_and_scope(self):
        answers = [
            "Africa was discussed first, but North America actually published more articles.",
            "Africa was the region we examined first.",
            "Africa was first mentioned in the report.",
            "Africa ranked first alphabetically.",
            "Africa had fewer articles than North America. Final answer: Africa.",
            "North America had more World articles than Africa. The answer is Africa.",
            "The answer is Africa, Europe or Asia.",
            "Did Africa publish the most World articles?",
            "Could Africa have the highest count?",
            "1. Africa (maybe)\n2. North America",
            "1. Africa\n2. Africa",
            "Africa isn’t the winner.",
            "Africa wasn’t ranked first.",
            "Africa didn’t publish the most World articles.",
            "Final answer: Not Africa.",
            "Africa published more articles than North America.",
            "Africa ranked first in 2014.",
            "Africa had the most Sports articles.",
            "Africa had the highest population.",
            "Africa had the highest count of countries.",
            "2014 World article counts:\nAfrica: 321\nNorth America: 319",
            "| Region | Population |\n|---|---|\n| Africa | 321 |\n| Asia | 319 |",
            "Africa had the most articles. Africa: 319, North America: 321.",
            "Africa: 319\nNorth America: 321\nFinal answer: Africa.",
            "Africa or North America tied for first.",
            "Africa was first in line.",
            "Africa ranked first in height.",
            "Africa is the winner, hypothetically.",
            "The answer is Africa, or possibly some other region.",
            "1. Africa (or North America)\n2. Europe",
            "1. Africa by height\n2. North America",
            "Height:\nAfrica: 321\nNorth America: 319",
            "Maybe Africa: 321, North America: 319.",
            "Africa: 321, North America: 319 (maybe).",
            "Africa ranked first, but not for World articles.",
            "2014 rankings:\nAfrica ranked first.",
            "Population:\nAfrica",
            "Perhaps these counts are correct:\nAfrica: 321\nNorth America: 319",
            "Africa ranked first. However, North America published the most World articles.",
            "Africa ranked first. It did not publish the most World articles.",
            "Africa had the highest count. North America led in the World category.",
        ]
        for answer in answers:
            with self.subTest(answer=answer):
                self.assertFalse(MODULE.validate(answer)[0])

    def test_region_substitution_changes_the_selected_winner(self):
        templates = [
            "{region} published the most World articles in 2015.",
            "In 2015, {region} published more World articles than any other region.",
            "{region} came out on top.",
            "The answer is **{region}**.",
            "1. {region}\n2. {runner_up}",
            "- {region}: 321\n- {runner_up}: 319",
        ]
        for region in ["Africa", "North America", "South America", "Europe", "Asia"]:
            runner_up = "North America" if region == "Africa" else "Africa"
            for template in templates:
                answer = template.format(region=region, runner_up=runner_up)
                with self.subTest(answer=answer):
                    self.assertEqual(MODULE.validate(answer)[0], region == "Africa")


if __name__ == "__main__":
    unittest.main()
