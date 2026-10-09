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
NUMBER = r"\d+(?:,\d{3})*"
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
    r"uncertain|whether|assuming|suppose|if)\b"
)
NEGATION = re.compile(r"\b(?:not|never|neither|cannot)\b")
LABEL = re.compile(
    r"^(?:the\s+)?(?:final\s+)?(?:answer|region|winning region|top region|winner)"
    r"\s*(?:is|was|:|=)\s*"
)
COUNT_ROW = re.compile(
    rf"\|?\s*({REGION})\s*(?:\||:|[-–—])\s*({NUMBER})"
    rf"\s*(?:{ARTICLES})?\s*\|?"
)
COUNT_ITEM = re.compile(rf"\b({REGION})\s*(?::|\bat\b)?\s+({NUMBER})\b")
RANK_ROW = re.compile(r"(\d+)[.)]\s+(.+)")
COMPARISON = re.compile(
    rf"^(?:has|had|have|{PUBLISH})\s+(more|fewer|less)\s+{ARTICLES}"
    rf"\s+than\s+({REGION_LIST})\b"
)


def _names(text):
    return {" ".join(match[0].split()) for match in REGIONS.finditer(text)}


def _normalize(text):
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    text = re.sub(r"[*`_]", "", text)
    text = re.sub(r"\b(is|was|are|were|does|do|did|has|have|had)n['’]t\b", r"\1 not", text)
    return text


def _in_scope(text):
    """An explicitly different year/category/metric cannot establish this answer."""
    years = set(re.findall(
        r"\b(?:in|for|during|year)\s+(?:the\s+year\s+)?((?:19|20)\d{2})\b", text
    ))
    heading_year = re.match(r"^((?:19|20)\d{2})\s+", text)
    if heading_year:
        years.add(heading_year[1])
    if years and years != {"2015"}:
        return False
    if re.search(r"\b(?:population|countries|gdp|revenue|land area|alphabetically|"
                 r"alphabetical|examined|discussed|mentioned|visited)\b", text):
        return False
    if re.search(r"\b(?:sports|business|science|technology)\b", text):
        return False
    return True


def _without_comparison(text):
    return re.split(
        r"\b(?:followed\s+(?:closely\s+)?by|ahead\s+of|compared\s+(?:to|with)|"
        r"rather\s+than|instead\s+of)\b|,\s*not\b", text, maxsplit=1
    )[0].rstrip(" ,(")


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
    if not clause or "?" in clause:
        return empty
    clause = re.sub(r"^(?:in|for|during)\s+2015\s*[:,]?\s*", "", clause)
    head = _without_comparison(clause)
    if not _in_scope(head):
        return empty
    # An unparsed competing assertion must not silently disappear merely
    # because a different sentence contains an accepted "Answer: Africa".
    potential_rank = bool(
        (REGIONS.search(head) or re.match(r"^(?:it|this region|that region)\b", head))
        and re.search(r"\b(?:first|most|largest|highest|greatest|winner|led|"
                      r"second|third|fewer|more)\b", head)
    )
    unsupported = (set(), set(), potential_rank)

    # Recognize negative short answers, including the form used after a label.
    labelled = LABEL.match(head)
    body = head[labelled.end():] if labelled else head
    if re.fullmatch(rf"not\s+({REGION_LIST})", body):
        return set(), _names(body), False

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


def validate(llm_output: str):
    text = _normalize(llm_output)
    groups, denied, counts, ranked = [], set(), {}, set()
    count_observations = []
    ambiguous = False
    table_in_scope = True

    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-+•]\s+|#+\s*)", "", line).strip()
        if not line:
            table_in_scope = True
            continue
        if not REGIONS.search(line) and (line.endswith(":") or line.startswith("|")):
            # Table/list headings can specify a different year or metric.
            if not re.fullmatch(r"[| :\-]+", line):
                table_in_scope = _heading_in_scope(line)
            continue

        rank = RANK_ROW.fullmatch(line)
        if rank:
            if not table_in_scope or not _in_scope(rank[2]):
                continue
            subject = SUBJECT.match(rank[2])
            if not subject:
                ambiguous = True
                continue
            regions = _names(subject[1])
            if UNCERTAIN.search(rank[2]) or re.search(r"\bor\b", subject[1]):
                ambiguous = True
            elif NEGATION.search(rank[2]) or LOWER_RANK.search(subject[2]):
                denied.update(regions)
            elif not _answer_tail(subject[2]):
                ambiguous = True
            elif int(rank[1]) == 1:
                ranked.update(regions)
            else:
                denied.update(regions)
            continue

        row = COUNT_ROW.fullmatch(line)
        if row:
            if table_in_scope:
                count_observations.append((row[1], row[2]))
            continue
        if not table_in_scope:
            continue

        # Keep question marks and coordinated region lists intact. A comma is
        # a clause boundary only before another region with its own predicate.
        clauses = re.split(
            rf"(?<=[.!?])\s+|;\s*|\b(?:but|whereas|while)\b(?=\s*{REGION}\b)|"
            rf",\s*(?={REGION}\s+(?:had|has|is|was|ranked|published)\b)", line
        )
        for clause in clauses:
            matches = list(COUNT_ITEM.finditer(clause))
            prefix = clause[:matches[0].start()].strip() if matches else ""
            count_list = not prefix or (prefix.endswith(":") and _heading_in_scope(prefix))
            if len(matches) > 1 and count_list and _in_scope(clause) and table_in_scope:
                if UNCERTAIN.search(clause) or NEGATION.search(clause) or "?" in clause:
                    ambiguous = True
                else:
                    count_observations.extend((match[1], match[2]) for match in matches)
            winners, losers, uncertain = _prose_claim(clause)
            if winners:
                groups.append(winners)
            denied.update(losers)
            ambiguous |= uncertain

    for region, number in count_observations:
        region = " ".join(region.split())
        number = int(number.replace(",", ""))
        if region in counts and counts[region] != number:
            return False, "Conflicting article counts for the same region."
        counts[region] = number
    if ranked:
        groups.append(ranked)
    if len(counts) > 1:
        maximum = max(counts.values())
        groups.append({region for region, count in counts.items() if count == maximum})
    if ambiguous:
        return False, "The answer contains an uncertain, alternative or unsupported ranking claim."
    if "africa" in denied:
        return False, "The answer denies Africa first place or puts another region above it."
    if not groups:
        return False, "No supported, affirmative first-place answer was found."
    if not all("africa" in group for group in groups):
        return False, "The answer selects another region above Africa or has conflicting winners."
    return True, "Africa is selected in first place; explicit ties are allowed."
