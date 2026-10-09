"""Regression tests for answer-region validation, including contextual mentions."""

import importlib.util
from itertools import permutations, product
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


    def test_evidence_and_scope_regressions(self):
        cases = [
            (False, '1. Africa (307 articles)\n2. North America (321 articles)'),
            (False, 'Africa and North America tied for first.\nAfrica: 321\nNorth America: 319'),
            (False, 'Africa and North America tied for first. North America was second.'),
            (False, '1. Africa\n2. North America\n3. North America'),
            (False, '1. Africa\n0. North America'),
            (False, 'Africa: 3.5, North America: 3.4'),
            (False, 'Africa: 1,23, North America: 1'),
            (False, 'Africa: 321\nNorth America: -10\nFinal answer: Africa.'),
            (False, 'Africa: 321\nNorth America: unknown\nFinal answer: Africa.'),
            (False, 'Africa: 321\nAtlantis: 400\nNorth America: 300'),
            (False, 'Africa: 321, North America: 319 (estimated)'),
            (False, 'Population:\n\nAfrica: 321\nNorth America: 319'),
            (False, '2014 World article counts:\n\nAfrica: 321\nNorth America: 319'),
            (False, 'Africa. Actually, no.'),
            (False, 'Africa. That is incorrect.'),
            (False, 'Africa. It is not.'),
            (False, 'Africa. North-America ranked first.'),
            (False, 'Africa. NorthAmerica ranked first.'),
            (False, 'Africa. Atlantis ranked first.'),
            (False, 'For example: Africa ranked first.'),
            (False, 'Africa / North America'),
            (False, 'Africa, rather than North America, which actually ranked first.'),
            (False, 'Africa ranked first, followed by North America in first place.'),
            (False, 'Africa ranked first, ahead of North America if the estimate is correct.'),
            (False, '1. Africa (tied with North America or Europe)'),
            (False, '| Region | Height |\n|---|---|\n| Africa | 321 |\n| Asia | 319 |'),
            (False, 'Africa.\n| Region | Rank | World articles |\n|---|---|---|\n| Africa | 2 | 319 |\n| North America | 1 | 321 |'),
            (True, '| Region | Rank | World articles |\n|---|---|---|\n| Africa | 1 | 321 |\n| North America | 2 | 319 |'),
            (True, '| World articles | Region |\n|---|---|\n| 321 | Africa |\n| 319 | North America |'),
            (True, '| Rank | Region |\n|---|---|\n| 1 | Africa |\n| 2 | North America |'),
            (True, 'Africa had the most World articles in 2015.\n2014 World article counts:\nAfrica: 10\nNorth America: 20'),
            (True, 'Africa and North‑America tied for first.'),
            (True, 'The winner is Africa.'),
            (True, 'Final answer:\nAfrica'),
            (True, 'Africa\xa0ranked\xa0first.'),
            (False, '0 Africa\n1 North America'),
            (False, 'The answer is Africa. Africa is not number one.'),
            (False, '"Africa is the winner" is false.'),
            (False, 'Africa ranked first. However, this is for Sports articles.'),
            (False, 'Africa is n\u200bot the winner.'),
            (False, 'Africa. No.'),
            (False, 'Africa. The real leader is North America.'),
            (False, 'Africa. North America tops the list.'),
            (False, 'Africa. North America came in first.'),
            (False, 'Africa. But the answer is North America.'),
            (False, 'Africa. I retract that answer.'),
            (False, 'Africa. This was just a guess.'),
            (False, 'Africa\nAtlantis: unknown'),
            (False, 'Africa\nAtlantis: -3'),
            (False, 'Africa\nAtlantis - 400\nNorth America: 200'),
            (False, 'Africa: 320\nNorth America - 400'),
            (False, 'Africa\n1. Africa\n-1. North America'),
            (False, 'Africa\n1. Africa\n2.5. North America'),
            (False, 'Africa\n1. Africa\n2. North America (319 articles)\n3. Europe (320 articles)'),
            (False, 'Africa ranked first with 310 articles, followed by North America with 320 articles.'),
            (False, 'Africa ranked first. North America and Europe tied for second; North America: 319, Europe: 318.'),
            (False, 'Africa. North America had 500 articles. Africa had 400 articles.'),
            (False, 'Africa.\n| Region | World articles |\n|---|---|\n| Africa | 300 |\n| North America | 400 |'),
            (False, 'Maybe:\nAfrica'),
            (False, 'Africa. It might be wrong.'),
            (False, 'Africa. However, the counts are estimates.'),
            (False, 'Africa. Answer: Asia?'),
            (False, 'Africa is first. Africa had exactly 321 articles; North America had exactly 400 articles.'),
            (True, 'Africa ranked first. Europe: 200, Asia: 100.'),
            (True, 'Africa: 321; North America: 319.'),
            (True, 'Africa and North America tied for first. Africa: 321, North America: 321.'),
            (True, 'Africa ranked first with 321 articles, followed by North America with 319 articles.'),
            (True, 'Africa. North America was second. Europe was third.'),
            (True, 'World article counts:\nAfrica: 321\nNorth America: 319'),
            (True, 'Africa ranked first. The counts were computed from the dataset.'),
        ]
        for expected, answer in cases:
            with self.subTest(answer=answer):
                self.assertEqual(MODULE.validate(answer)[0], expected)

    def test_count_order_and_format_matrix(self):
        regions = ["Africa", "North America", "South America", "Europe", "Asia"]
        for left, right in permutations(regions, 2):
            for left_count, right_count in product([319, 320, 321], repeat=2):
                expected = ((left == "Africa" and left_count >= right_count)
                            or (right == "Africa" and right_count >= left_count))
                answers = [
                    f"{left}: {left_count}, {right}: {right_count}.",
                    f"- {left}: {left_count}\n- {right}: {right_count}",
                    f"| Region | World articles |\n|---|---|\n| {left} | {left_count} |\n| {right} | {right_count} |",
                    f"| Count | Region |\n|---|---|\n| {left_count} | {left} |\n| {right_count} | {right} |",
                ]
                for answer in answers:
                    with self.subTest(answer=answer):
                        self.assertEqual(MODULE.validate(answer)[0], expected)

    def test_rank_count_consistency_matrix(self):
        for other, other_rank, other_count, reverse in product(
                ["North America", "South America", "Europe", "Asia"], [1, 2], [319, 320, 321], [False, True]):
            # Africa is rank 1 with 320 articles. Ties require equal counts;
            # strictly lower ranks require strictly smaller counts.
            expected = ((other_rank == 1 and other_count == 320)
                        or (other_rank == 2 and other_count < 320))
            rows = [["Africa", "1", "320"], [other, str(other_rank), str(other_count)]]
            if reverse:
                rows.reverse()
            for columns in permutations(range(3)):
                headers = ["Region", "Rank", "World articles"]
                table = ["| " + " | ".join(headers[i] for i in columns) + " |", "|---|---|---|"]
                table.extend("| " + " | ".join(row[i] for i in columns) + " |" for row in rows)
                answer = "\n".join(table)
                with self.subTest(answer=answer):
                    self.assertEqual(MODULE.validate(answer)[0], expected)

    def test_malformed_count_matrix(self):
        malformed = ["-1", "3.5", "1,23", "12,34,567", "3e2", "NaN", "unknown",
                     "321 (estimated)", "321?", "321 or 322", "321abc", "321%", "9" * 5000]
        for value, bad_region, layout in product(malformed, ["Africa", "North America"], range(3)):
            counts = {"Africa": "321", "North America": "319"}
            counts[bad_region] = value
            rows = [f"{region}: {count}" for region, count in counts.items()]
            if layout == 0:
                body = "\n".join(rows)
            elif layout == 1:
                body = ", ".join(rows)
            else:
                body = "| Region | World articles |\n|---|---|\n" + "\n".join(
                    f"| {region} | {count} |" for region, count in counts.items())
            answer = "Final answer: Africa.\n" + body
            with self.subTest(value=value[:40], bad_region=bad_region, layout=layout):
                self.assertFalse(MODULE.validate(answer)[0])

    def test_competing_claim_and_normalization_matrix(self):
        templates = ["{region} ranked first.", "The answer is {region}.",
                     "{region} came out on top.", "{region} tops the list.",
                     "The real leader is {region}.", "However, {region} is the winner."]
        regions = ["North America", "South America", "Europe", "Asia",
                   "North-America", "SouthAmerica", "North‑America", "Atlantis"]
        for template, region, separator, reverse in product(templates, regions, [" ", "\n", "; "], [False, True]):
            claim = template.format(region=region)
            answer = claim + separator + "Africa." if reverse else "Africa." + separator + claim
            with self.subTest(answer=answer):
                self.assertFalse(MODULE.validate(answer)[0])

    def test_heading_scope_survives_whitespace_matrix(self):
        for heading, blank, marker, prefix in product(
                ["Population", "Height", "2014 World article counts", "Sports article counts"],
                ["\n", "\n\n", "\n \n"], ["", "## "], ["", "Africa ranked first.\n"]):
            answer = prefix + marker + heading + ":" + blank + "Africa: 321\nNorth America: 319"
            with self.subTest(answer=answer):
                self.assertEqual(MODULE.validate(answer)[0], bool(prefix))

    def test_section_transitions_and_conflicting_identity(self):
        cases = [
            (False, 'Africa. North America had the most World articles, not Sports articles.'),
            (False, 'Africa. North America ranked first in 2015, not in 2014.'),
            (False, 'Africa.\n2014 World article counts:\nAfrica: 300\nNorth America: 200\nFinal answer: North America.'),
            (False, 'Africa.\nPopulation:\nAfrica: 300\nNorth America: 200\nNorth America ranked first in 2015.'),
            (False, '2014 World article counts\nAfrica: 321\nNorth America: 319'),
            (False, '## 2014 World article counts\nAfrica: 321\nNorth America: 319'),
            (False, 'Africa.\n-1. Atlantis'),
            (False, 'Africa.\n1.5. Atlantis'),
            (False, 'Africa.\n| Region | World and Sports articles |\n|---|---|\n| North America | 400 |\n| Africa | 300 |'),
            (False, 'Africa.\nWorld and Sports article counts:\nNorth America: 400\nAfrica: 300'),
            (True, '2014 World article counts:\nAfrica: 300\nNorth America: 400\nFinal answer: Africa.'),
            (True, 'Population:\nAfrica: 300\nNorth America: 400\nAfrica ranked first in 2015.'),
            (True, '## World article counts\nAfrica: 321\nNorth America: 319'),
            (False, 'Africa. North America ranked first and second.'),
            (False, 'Africa. North America: 300\nNorth   America: 301'),
            (False, 'Africa.\n| Region | Rank |\n|---|---|\n| North America | 2 |\n| North   America | 3 |'),
            (True, 'Africa ranked first.\nNorth   America: 319\nNorth America: 319'),
        ]
        for expected, answer in cases:
            with self.subTest(answer=answer):
                self.assertEqual(MODULE.validate(answer)[0], expected)

    def test_observed_submission_answers(self):
        cases = [
            (True, 'In 2015, two regions tied for publishing the largest number of World-category articles: North America and Africa, each with 317 World articles. (For context: Europe had 315, South America had 315, and Asia had 304 World-category articles.)'),
            (True, 'In 2015, Africa published the largest number of World-category articles, with 307 World articles. The runner-up was South America with 301 World articles.\n\nFull breakdown of World-category articles by region in 2015:\n- Africa: 307\n- South America: 301\n- North America: 299\n- Asia: 295\n- Europe: 295\n\n(All 6696 articles published in 2015 were classified into World, Sports, Business, or Science/Technology based on their title and description text.)'),
            (False, 'In 2015, North America published the largest number of articles in the World category, with 321 World articles (followed closely by South America at 320, Africa at 319, Europe at 316, and Asia at 299).'),
            (True, 'In 2015, Africa published the largest number of articles in the World category (320 World-category articles out of 1570 total World articles across all 6696 articles published in 2015). The full regional breakdown of World-category articles in 2015: Africa 320, South America 318, North America 316, Europe 310, Asia 306.'),
            (True, 'In 2015, the region that published the largest number of articles in the World category was **Africa**, with 337 World-category articles.'),
        ]
        for run, (expected, answer) in enumerate(cases):
            with self.subTest(run=run):
                self.assertEqual(MODULE.validate(answer)[0], expected)

if __name__ == "__main__":
    unittest.main()
