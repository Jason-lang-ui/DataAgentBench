"""Recognize supported first-place claims for agnews/query4, including ties.

This is a deterministic grammar, not a general semantic judge. Unsupported prose
does not establish a correct answer. Explicit answers, predicates, rankings and
counts provide evidence; incidental region or superlative words do not.
"""

import re
import unicodedata


# Match qualified names as a whole: South Africa is not the region Africa.
REGION = (
    r"(?:(?:north|south)\s+america|"
    r"(?:(?:north|south|east|west|central)(?:ern)?\s+)?africa|"
    r"europe|asia|oceania|australia|antarctica)"
)
REGIONS = re.compile(rf"\b{REGION}\b")
REGION_LIST = rf"{REGION}(?:(?:\s*,\s*(?:and\s+)?|\s+(?:and|or|&)\s+){REGION})*"
SUBJECT = re.compile(rf"^({REGION_LIST})\b(.*)$")
NUMBER = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)"
ARTICLES = r"(?:(?:world(?:[ -]category)?|news)\s+)?articles"
MAXIMUM = (
    rf"(?:the\s+)?(?:most\s+{ARTICLES}|"
    rf"(?:largest|highest|greatest|maximum)\s+(?:number|count|total)"
    rf"(?:\s+(?:of\s+)?{ARTICLES})?)"
)
QUERY_CONTEXT = (
    r"(?:\s+(?:(?:in|for|during)\s+2015|"
    r"(?:in|for)\s+(?:the\s+)?world(?:[ -]category)?))*"
)
FIRST = r"(?:first(?:\s+place)?|1st(?:\s+place)?|number\s+one|no\.?\s*1|#1)"
PUBLISH = r"(?:publish(?:ed|es)?|produc(?:e|ed|es)|record(?:ed|s)?)"
WINNING_PREDICATE = re.compile(
    rf"^(?:(?:has|had|have|{PUBLISH})\s+{MAXIMUM}|"
    rf"(?:{PUBLISH}|has|had|have)\s+more\s+{ARTICLES}\s+than\s+"
    rf"(?:any|every|all)\s+other\s+regions?|"
    rf"(?:rank(?:ed|s)?|place(?:d|s)?|finish(?:ed|es)?|came)\s+{FIRST}|"
    rf"(?:is|was|were|are)\s+(?:ranked\s+)?(?:{FIRST}|(?:the\s+)?winner)|"
    rf"came\s+out\s+on\s+top|"
    rf"(?:is\s+|was\s+|were\s+|are\s+)?(?:tied|jointly\s+ranked)\s+"
    rf"(?:for\s+)?(?:{FIRST}|{MAXIMUM}))\b"
)
LOWER_RANK = re.compile(r"\b(?:second|third|fourth|fifth|last|runner[ -]up|lowest|least|fewest)\b")
UNCERTAIN = re.compile(
    r"\b(?:maybe|perhaps|might|may|could|possibly|probably|unclear|unsure|"
    r"uncertain|whether|assuming|suppose|if|estimated|approximately|roughly)\b"
)
NEGATION = re.compile(r"\b(?:not|never|neither|cannot)\b")
LABEL = re.compile(
    r"^(?:the\s+)?(?:final\s+)?(?:answer|region|winning region|top region|winner)"
    r"\s*(?:is|was|:|=)\s*"
)
RANK_ROW = re.compile(r"(\d+)[.)]\s+(.+)")
COMPARISON = re.compile(
    rf"^(?:has|had|have|{PUBLISH})\s+(more|fewer|less)\s+{ARTICLES}"
    rf"\s+than\s+({REGION_LIST})\b"
)


def _names(text):
    return {" ".join(match[0].split()) for match in REGIONS.finditer(text)}


def _normalize(text):
    text = unicodedata.normalize("NFKC", text).lower()
    text = "".join(char for char in text if unicodedata.category(char) != "Cf")
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    text = re.sub(r"[‐‑‒–—−]", "-", text)
    text = re.sub(r"\b(north|south)[ -]*america\b", r"\1 america", text)
    text = re.sub(r"[*`_]", "", text)
    text = re.sub(r"\b(is|was|are|were|does|do|did|has|have|had)n['’]t\b", r"\1 not", text)
    return text


def _years(text):
    years = set(re.findall(
        r"\b(?:in|for|during|year)\s+(?:the\s+year\s+)?((?:19|20)\d{2})\b", text
    ))
    heading_year = re.match(r"^((?:19|20)\d{2})\s+", text)
    if heading_year:
        years.add(heading_year[1])
    return years


def _mixed_scope(text):
    years = _years(text)
    return (("2015" in years and years != {"2015"})
            or (bool(re.search(r"\bworld\b", text))
                and bool(re.search(r"\b(?:sports|business|science|technology|population|gdp|height)\b", text))))


def _in_scope(text):
    """An explicitly different year/category/metric cannot establish this answer."""
    years = _years(text)
    if years and years != {"2015"}:
        return False
    if re.search(r"\b(?:population|countries|gdp|revenue|land area|alphabetically|"
                 r"alphabetical|examined|discussed|mentioned|visited)\b", text):
        return False
    if re.search(r"\b(?:sports|business|science|technology)\b", text):
        return False
    return True


def _without_comparison(text):
    parts = re.split(
        r"\b(?:followed\s+(?:closely\s+)?by|ahead\s+of|compared\s+(?:to|with)|"
        r"rather\s+than|instead\s+of)\b|,\s*not\b", text, maxsplit=1
    )
    if len(parts) == 2:
        # Only discard a plain list of comparison regions (optionally counts).
        # A trailing assertion or condition must remain visible to the parser.
        item = rf"{REGION}(?:\s+(?:at|with)\s+{NUMBER}(?:\s+{ARTICLES})?)?"
        tail = rf"{item}(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+){item})*"
        if not re.fullmatch(tail, parts[1].strip(" ,().")):
            return text
    return parts[0].rstrip(" ,(")


def _winner_predicate(text):
    match = WINNING_PREDICATE.match(text)
    if not match:
        return False
    return _answer_tail(text[match.end():])


def _answer_tail(text):
    """Only consume count, tie and question-scope adjuncts, not arbitrary prose."""
    adjunct = (
        rf"(?:(?:in|for|during)\s+2015|"
        rf"(?:in|for)\s+(?:the\s+)?world(?:[ -]category)?|"
        rf"(?:among|of)\s+(?:all\s+)?(?:the\s+)?regions|"
        rf"tied\s+with\s+{REGION_LIST}|tied|"
        rf"(?:each\s+)?(?:(?:with|at)\s+)?{NUMBER}\s+{ARTICLES}"
        rf"(?:\s+out\s+of\s+{NUMBER}\s+(?:total\s+)?{ARTICLES})?"
        rf"(?:\s+across\s+(?:all\s+)?{NUMBER}\s+articles(?:\s+published)?)?)\b"
    )
    text = text.strip(" ,:()")
    while text:
        match = re.match(adjunct, text)
        if not match:
            return False
        text = text[match.end():].strip(" ,:()")
    return True


def _heading_in_scope(text):
    return (
        _in_scope(text)
        and not UNCERTAIN.search(text)
        and not NEGATION.search(text)
        and "?" not in text
        and bool(re.search(r"\b(?:world|articles|counts?|rankings?|answer|results|breakdown)\b", text))
    )


def _reverse_winner(prefix):
    return bool(re.fullmatch(
        rf"(?:(?:the\s+)?(?:region\s+(?:with|that\s+{PUBLISH})\s+{MAXIMUM}{QUERY_CONTEXT}|"
        rf"winner|top\s+region)\s+(?:is|was)|"
        rf"(?:in\s+2015,?\s+)?(?:two|three|several)\s+regions\s+tied\s+for\s+"
        rf"(?:publishing\s+|having\s+)?{MAXIMUM}\s*:|"
        rf"{MAXIMUM}\s+(?:was|were)\s+published\s+by)\s*", prefix
    ))


def _prose_claim(clause):
    """Return (winning regions, non-winners, ambiguous) for one assertion."""
    empty = (set(), set(), False)
    clause = clause.strip(" \t\r\"'[]().!")
    clause = re.sub(r"^(?:and|but|however)\b\s*,?\s*", "", clause)
    if not clause:
        return empty
    if "?" in clause:
        return set(), set(), bool(REGIONS.search(clause) or LABEL.match(clause))
    # Retractions may refer to an earlier sentence without repeating its region.
    if clause == "no" or re.search(r"\b(?:retract|withdraw|guess|estimates|"
                 r"actually\s*,?\s*no|(?:that|this|it|the answer)\s+"
                 r"(?:is|was)\s+(?:not|incorrect|wrong|false|for)|"
                 r"(?:however|correction)\s*[:,].*\b(?:this|that|it)\b)", clause):
        return set(), set(), True
    clause = re.sub(r"^(?:in|for|during)\s+2015\s*[:,]?\s*", "", clause)
    head = _without_comparison(clause)
    if _mixed_scope(head) and REGIONS.search(head):
        return set(), set(), True
    if not _in_scope(head):
        return empty
    # An unparsed competing assertion must not silently disappear merely
    # because a different sentence contains an accepted "Answer: Africa".
    potential_rank = bool(
        REGIONS.search(head) or LABEL.match(head) or UNCERTAIN.search(head)
        or re.search(r"\b(?:first|most|largest|highest|greatest|winner|leader|led|tops?|"
                     r"second|third|fewer|more)\b", head)
    )
    unsupported = (set(), set(), potential_rank)

    # Recognize negative short answers, including the form used after a label.
    labelled = LABEL.match(head)
    body = head[labelled.end():] if labelled else head
    if re.fullmatch(rf"not\s+({REGION_LIST})", body):
        return set(), _names(body), False
    runner_up = re.fullmatch(rf"(?:the\s+)?runner[ -]up\s+(?:is|was)\s+({REGION})(.*)", body)
    if runner_up and _answer_tail(runner_up[2]):
        return set(), _names(runner_up[1]), False

    uncertain = bool(UNCERTAIN.search(head))
    body = re.sub(r"^(?:maybe|perhaps|possibly|probably)\s+", "", body)
    subject = SUBJECT.match(body)
    reverse = False
    if not subject:
        first = REGIONS.search(body)
        if not first or not _reverse_winner(body[:first.start()]):
            return unsupported
        subject = SUBJECT.match(body[first.start():])
        reverse = True
    regions = _names(subject[1])
    predicate = subject[2].strip()
    alternatives = bool(re.search(r"\bor\b", subject[1]))
    negative = bool(NEGATION.search(head))

    # Comparative evidence can disprove a claimed winner without naming the
    # global maximum: "North America had more articles than Africa" is enough.
    comparison = COMPARISON.match(predicate)
    if comparison and not negative:
        losers = regions if comparison[1] in {"fewer", "less"} else _names(comparison[2])
        return set(), losers, uncertain or alternatives

    next_region = REGIONS.search(predicate)
    local_predicate = predicate[:next_region.start()] if next_region else predicate
    lower = bool(LOWER_RANK.search(local_predicate))
    if lower and not negative:
        if re.search(rf"\b{FIRST}\b", local_predicate):
            return set(), set(), True
        return set(), regions, uncertain or alternatives

    positive_predicate = NEGATION.sub("", predicate)
    positive_predicate = re.sub(r"^(?:did|does|do)\s+", "", positive_predicate)
    positive_predicate = " ".join(positive_predicate.split())
    counted = bool(re.fullmatch(
        rf"[,:(]\s*(?:with\s+)?{NUMBER}\s+{ARTICLES}\)?", predicate
    ))
    winner = (
        not predicate or ((bool(labelled) or reverse) and _answer_tail(predicate)) or counted
        or _winner_predicate(positive_predicate)
    )
    if not winner:
        return unsupported
    if uncertain or alternatives:
        return set(), set(), True
    if negative:
        return set(), regions, False

    tie = re.search(rf"\btied\s+with\s+({REGION_LIST})", predicate)
    if tie:
        if re.search(r"\bor\b", tie[1]):
            return set(), set(), True
        regions.update(_names(tie[1]))
    return regions, set(), False


class _Evidence:
    """Keep independent observations so no conflicting row can be overwritten."""

    def __init__(self):
        self.groups = []
        self.denied = set()
        self.counts = {}
        self.ranks = {}
        self.ambiguous = False

    def number(self, region, value, rank=False):
        region = " ".join(region.split())
        if not REGIONS.fullmatch(region) or not re.fullmatch(NUMBER, value):
            self.ambiguous = True
            return
        digits = value.replace(",", "")
        # Counts in this dataset are small; avoid unbounded integer conversions.
        if len(digits) > 15:
            self.ambiguous = True
            return
        number = int(digits)
        if rank and number < 1:
            self.ambiguous = True
            return
        observations = self.ranks if rank else self.counts
        if region in observations and observations[region] != number:
            self.ambiguous = True
        observations[region] = number
        if rank and number > 1:
            self.denied.add(region)

    def result(self):
        first = {region for region, rank in self.ranks.items() if rank == 1}
        if first:
            self.groups.append(first)
        if len(self.counts) > 1:
            maximum = max(self.counts.values())
            leaders = {region for region, count in self.counts.items() if count == maximum}
            # Every member of a claimed tie must agree with observed counts.
            for group in self.groups:
                if any(region in self.counts and region not in leaders for region in group):
                    self.ambiguous = True
            if not self.groups or "africa" in self.counts:
                self.groups.append(leaders)
        common = self.ranks.keys() & self.counts.keys()
        for left in common:
            for right in common:
                rank_delta = self.ranks[left] - self.ranks[right]
                count_delta = self.counts[left] - self.counts[right]
                if ((rank_delta == 0 and count_delta != 0)
                        or (rank_delta != 0 and rank_delta * count_delta >= 0)):
                    self.ambiguous = True
        if any(group & self.denied for group in self.groups):
            return False, "A stated winner is also denied first place."
        if self.ambiguous:
            return False, "Uncertain, unsupported or conflicting ranking/count evidence."
        if not self.groups:
            return False, "No supported, affirmative first-place answer was found."
        if not all("africa" in group for group in self.groups):
            return False, "The answer selects another region above Africa or has conflicting winners."
        return True, "Africa is selected in first place; explicit ties are allowed."


def _count_list(clause, evidence):
    """Consume an entire count list, never just valid-looking numeric prefixes.

    Return whether this clause has count-list syntax, including malformed lists.
    Numeric prose is handled separately from explicit first-place assertions.
    """
    body = clause.strip(" ()")
    body = re.sub(r"^(?:and|but|however)\b\s*,?\s*", "", body)
    if body.endswith("."):
        body = body[:-1]
    prefix = re.match(r"^([^:]+):\s*", body)
    if (prefix and not REGIONS.search(prefix[1])
            and re.search(r"\b(?:counts?|breakdown|context|results)\b", prefix[1])
            and not re.search(r"\b(?:most|largest|highest|first|tied)\b", prefix[1])):
        body = body[prefix.end():]
    candidate = re.match(rf"^(?:{REGION}\s*(?::|\s+(?:(?:at|had|has)\s+)?[0-9-])|[a-z ]+\s*[:\-]\s*(?:[-0-9]|unknown|nan|n/a))", body)
    if not candidate:
        return False
    item = re.compile(rf"({REGION})\s*(?::\s*|(?:at|had|has)\s+|\s+)({NUMBER})(?:\s+{ARTICLES})?")
    observations = []
    while body:
        match = item.match(body)
        if not match:
            evidence.ambiguous = True
            return True
        observations.append((match[1], match[2]))
        body = body[match.end():]
        if not body:
            break
        separator = re.match(r"(?:\s*,\s*(?:and\s+)?|\s+and\s+)", body)
        if not separator or not body[separator.end():]:
            evidence.ambiguous = True
            return True
        body = body[separator.end():]
    for region, count in observations:
        evidence.number(region, count)
    return True


def _table_schema(cells):
    roles = []
    for cell in cells:
        if re.fullmatch(r"regions?", cell):
            roles.append("region")
        elif re.fullmatch(r"rank|ranking|position", cell):
            roles.append("rank")
        elif re.fullmatch(rf"(?:(?:world(?:[ -]category)?\s+)?(?:article\s+)?counts?|{ARTICLES}|number of {ARTICLES})", cell):
            roles.append("count")
        else:
            roles.append(None)
    if roles.count("region") == 1 and all(role is not None for role in roles) and len(set(roles)) == len(roles) and len(roles) > 1:
        return roles
    return None


def validate(llm_output: str):
    if not isinstance(llm_output, str):
        return False, "The answer must be text."
    text = _normalize(llm_output)
    evidence = _Evidence()
    section_in_scope = True
    table_roles = None
    table_active = False
    table_in_scope = True

    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-+•]\s+|#+\s*)", "", line).strip()
        if not line:
            # Blank lines do not cancel an explicit year/category/metric heading.
            continue
        if "|" in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                continue
            if any(re.fullmatch(r"regions?", cell) for cell in cells):
                table_active = True
                table_roles = _table_schema(cells)
                table_in_scope = section_in_scope and _in_scope(line)
                evidence.ambiguous |= _mixed_scope(line)
                # Unknown metric columns cannot establish article rankings.
                # A partially recognized ranking table is unsafe to ignore.
                if table_in_scope and table_roles is None and any(re.search(r"\b(?:rank|articles|count)\b", cell) for cell in cells):
                    evidence.ambiguous = True
                continue
            if table_active:
                if not table_in_scope or table_roles is None:
                    continue
                if len(cells) != len(table_roles):
                    evidence.ambiguous = True
                    continue
                row = dict(zip(table_roles, cells))
                for role in ("count", "rank"):
                    if role in row:
                        evidence.number(row["region"], row[role], rank=role == "rank")
                continue
            # A headerless table's column meaning cannot safely be inferred.
            if section_in_scope:
                evidence.ambiguous = True
            continue
        table_active = False
        table_roles = None
        heading = line.endswith(":") or re.search(r"\b(?:counts?|rankings?|population|height)$", line)
        if not REGIONS.search(line) and heading:
            evidence.ambiguous |= _mixed_scope(line)
            section_in_scope = _heading_in_scope(line)
            continue
        # A new explicit answer or question-year assertion ends a background
        # section; an empty line by itself does not.
        if LABEL.match(line) or (REGIONS.search(line) and _years(line) == {"2015"}):
            section_in_scope = True
        if not section_in_scope:
            continue

        rank = RANK_ROW.fullmatch(line)
        if rank:
            if not _in_scope(rank[2]):
                continue
            subject = SUBJECT.match(rank[2])
            if (not subject or UNCERTAIN.search(rank[2]) or NEGATION.search(rank[2])
                    or re.search(r"\bor\b", rank[2]) or not _answer_tail(subject[2])):
                evidence.ambiguous = True
                continue
            regions = _names(subject[1])
            tie = re.search(rf"\btied\s+with\s+({REGION_LIST})", subject[2])
            if tie:
                regions.update(_names(tie[1]))
            count = re.search(rf"\b({NUMBER})\s+{ARTICLES}\b", subject[2])
            for region in regions:
                evidence.number(region, rank[1], rank=True)
                if count:
                    evidence.number(region, count[1])
            continue

        if re.match(r"^[+-]?[0-9]+(?:\.[0-9]+)?[.)]\s+", line):
            evidence.ambiguous = True
            continue

        # Keep decimal points and coordinated region lists intact.
        clauses = re.split(
            rf"(?<=[.!?])\s+|;\s*|\b(?:but|whereas|while)\b(?=\s*{REGION}\b)|"
            rf",\s*(?={REGION}\s+(?:had|has|is|was|ranked|published)\b)", line
        )
        for clause in clauses:
            if _in_scope(clause) and _count_list(clause, evidence):
                continue
            winners, losers, uncertain = _prose_claim(clause)
            if winners:
                evidence.groups.append(winners)
                # A count attached to a supported first-place claim also
                # constrains subsequent rankings and tables (including ties).
                head = _without_comparison(clause)
                count = re.search(rf"\b({NUMBER})\s+{ARTICLES}\b", head)
                if count:
                    for region in winners:
                        evidence.number(region, count[1])
                if head != clause:
                    for item in re.finditer(rf"({REGION})\s+(?:at|with)\s+({NUMBER})", clause[len(head):]):
                        evidence.number(item[1], item[2])
            # Preserve explicit lower-place ties and positions as well as first
            # place, so their accompanying counts cannot contradict each other.
            if not uncertain and (winners or losers):
                ordinal = re.search(r"\b(first|second|third|fourth|fifth|1st|2nd|3rd)\b", clause)
                if ordinal and not NEGATION.search(clause):
                    positions = {"first": 1, "1st": 1, "second": 2, "2nd": 2,
                                 "third": 3, "3rd": 3, "fourth": 4, "fifth": 5}
                    for region in winners or losers:
                        evidence.number(region, str(positions[ordinal[1]]), rank=True)
            evidence.denied.update(losers)
            evidence.ambiguous |= uncertain

    return evidence.result()
