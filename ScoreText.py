import re
from difflib import get_close_matches


STAT_RULES = {
    "Crit. Rate": {
        "max_value": 10.5,
        "max_score": 10,
    },
    "Crit. DMG": {
        "max_value": 21.0,
        "max_score": 8,
    },
    "ATK%": {
        "max_value": 11.6,
        "max_score": 7,
    },
    "HP%": {
        "max_value": 11.6,
        "max_score": 5,
    },
    "DEF%": {
        "max_value": 14.7,
        "max_score": 5,
    },
    "Energy Regen": {
        "max_value": 12.4,
        "max_score": 5,
    },
    "Basic Attack DMG Bonus": {
        "max_value": 11.6,
        "max_score": 5,
    },
    "Heavy Attack DMG Bonus": {
        "max_value": 11.6,
        "max_score": 5,
    },
    "Resonance Skill DMG Bonus": {
        "max_value": 11.6,
        "max_score": 5,
    },
    "Resonance Liberation DMG Bonus": {
        "max_value": 11.6,
        "max_score": 5,
    },
}


VALID_STAT_NAMES = list(STAT_RULES.keys())


def clean_line(line: str) -> str:
    line = line.strip()
    line = line.lstrip("+").strip()
    line = re.sub(r"\s+", " ", line)
    return line


def extract_value(line: str):
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*%?", line)

    if not matches:
        return None

    return float(matches[-1])


def extract_stat_name(line: str):
    stat_name = re.sub(r"\d+(?:\.\d+)?\s*%?\s*$", "", line).strip()

    replacements = {
        "Crit Rate": "Crit. Rate",
        "CRIT Rate": "Crit. Rate",
        "Crit. Rale": "Crit. Rate",
        "Crit. Dmg": "Crit. DMG",
        "Crit DMG": "Crit. DMG",
        "CRIT DMG": "Crit. DMG",
        "Crit. DMC": "Crit. DMG",
        "Atk": "ATK%",
        "ATK": "ATK%",
        "HP": "HP%",
        "DEF": "DEF%",
    }

    if stat_name in replacements:
        return replacements[stat_name]

    return stat_name


def match_stat_name(raw_name: str):
    if raw_name in STAT_RULES:
        return raw_name

    matches = get_close_matches(
        raw_name,
        VALID_STAT_NAMES,
        n=1,
        cutoff=0.65
    )

    if matches:
        return matches[0]

    return None


def calculate_substat_score(stat_name: str, value: float):
    rule = STAT_RULES[stat_name]

    max_value = rule["max_value"]
    max_score = rule["max_score"]

    score = value / max_value * max_score

    # Do not allow OCR errors to exceed top score
    score = min(score, max_score)

    return score


def calculate_strength_from_lines(lines: list[str]) -> float:
    total_score = 0.0

    for line in lines:
        cleaned = clean_line(line)

        if not cleaned:
            continue

        value = extract_value(cleaned)
        raw_stat_name = extract_stat_name(cleaned)
        matched_stat_name = match_stat_name(raw_stat_name)

        if value is None:
            print(f"Failed to read value: {cleaned}")
            continue

        if matched_stat_name is None:
            print(f"Unknown stat name: {raw_stat_name}")
            continue

        score = calculate_substat_score(matched_stat_name, value)
        total_score += score

        print(
            f"{matched_stat_name}: "
            f"{value}% -> "
            f"{score:.2f}"
        )

    strength_percent = total_score / 35 * 100

    return strength_percent