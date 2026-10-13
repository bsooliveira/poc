import re


def sentences(text):
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])|\n+", text)
        if part.strip()
    ]


def coverage_key(text):
    return re.sub(r"\s+", " ", text).strip().casefold()
