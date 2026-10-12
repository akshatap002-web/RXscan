"""Rule + fuzzy-matching extraction of medicines from OCR lines.

`index` is a list of (lowercase_name, medicine_key) covering generic and brand names.
"""
import re
from difflib import SequenceMatcher

PREFIX = re.compile(r"^\s*(?:tab(?:let)?s?|cap(?:sule)?s?|syp|syrup|inj(?:ection)?|susp(?:ension)?|"
                    r"drops?|oint(?:ment)?|cream|gel)\b\.?\s*", re.I)
NUMBERING = re.compile(r"^\s*\(?\d{1,2}[\).:]\s+")
STRENGTH = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|m9|mcg|µg|ug|g|ml|iu)\b", re.I)
FREQ = re.compile(r"(?<!\d)([0-3]\s*[-–]\s*[0-3]\s*[-–]\s*[0-3](?:\s*[-–]\s*[0-3])?)(?!\d)|"
                  r"\b(OD|BD|BID|TDS|TID|QID|QDS|HS|SOS|PRN|STAT)\b", re.I)
DURATION = re.compile(r"(?:x|for)?\s*(\d+)\s*(days?|d|weeks?|wks?|months?)\b", re.I)
WORD = re.compile(r"[A-Za-z]{4,}")

STOPWORDS = {
    "patient", "name", "date", "age", "years", "year", "male", "female", "doctor", "hospital",
    "clinic", "after", "before", "food", "meal", "meals", "morning", "night", "noon", "days",
    "daily", "dose", "doses", "tablet", "tablets", "capsule", "capsules", "syrup", "with",
    "water", "take", "twice", "thrice", "once", "weeks", "week", "month", "signature", "address",
    "phone", "regd", "sign", "review", "follow", "advice", "diagnosis", "weight", "fever", "pain",
}


def _score(a, b):
    return SequenceMatcher(None, a, b).ratio() * 100


def best_matches(token, index, top=3):
    """Return up to `top` distinct medicines as [(key, score)] sorted by score."""
    token = token.lower()
    best = {}
    for name, key in index:
        s = _score(token, name)
        if key not in best or s > best[key]:
            best[key] = s
    return sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:top]


def _clean_line(text):
    text = NUMBERING.sub("", text)
    has_prefix = bool(PREFIX.match(text))
    text = PREFIX.sub("", text)
    return text, has_prefix


def _extract_fields(text):
    strength = freq = duration = ""
    m = STRENGTH.search(text)
    if m:
        unit = m.group(2).lower().replace("µg", "mcg").replace("ug", "mcg").replace("m9", "mg")
        strength = f"{m.group(1)} {unit}"
    m = FREQ.search(text)
    if m:
        freq = re.sub(r"\s+", "", (m.group(1) or m.group(2))).replace("–", "-").upper()
    m = DURATION.search(text)
    if m:
        unit = m.group(2).lower()
        unit = "days" if unit.startswith("d") else ("weeks" if unit.startswith("w") else "months")
        duration = f"{m.group(1)} {unit}"
    return strength, freq, duration


def parse_lines(lines, index):
    items = []
    current = None
    for line in lines:
        raw = line["text"]
        text, has_prefix = _clean_line(raw)
        strength, freq, duration = _extract_fields(text)
        tokens = [t for t in WORD.findall(text) if t.lower() not in STOPWORDS
                  and not re.fullmatch(r"(?:mg|mcg|days?|weeks?)", t.lower())]

        top, token = [], None
        for t in tokens:
            matches = best_matches(t, index)
            if matches and (not top or matches[0][1] > top[0][1]):
                top, token = matches, t

        threshold = 72 if (token and len(token) >= 6) else 85
        is_new = bool(token) and (has_prefix or (top and top[0][1] >= threshold))

        if is_new:
            score = top[0][1] if top else 0
            matched = score >= 60
            conf = round(0.8 * score + 0.2 * line["conf"], 1) if matched else round(0.8 * score, 1)
            current = {
                "detected_text": token,
                "best": top[0][0] if matched else None,
                "alternatives": [{"key": k, "score": round(s, 1)} for k, s in top],
                "confidence": conf,
                "ocr_conf": round(line["conf"], 1),
                "strength": strength, "frequency": freq, "duration": duration,
            }
            items.append(current)
        elif current is not None:
            # continuation line: fill in the missing dosage fields only
            current["strength"] = current["strength"] or strength
            current["frequency"] = current["frequency"] or freq
            current["duration"] = current["duration"] or duration
    return items
