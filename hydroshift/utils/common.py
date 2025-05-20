from itertools import groupby
from typing import List

import pandas as pd

from hydroshift.consts import REGULATION_MAP


def num_2_word(number: int) -> str:
    """Convert numbers less than 10 to words."""
    if number > 9:
        return number
    else:
        d = {
            0: "no",
            1: "one",
            2: "two",
            3: "three",
            4: "four",
            5: "five",
            6: "six",
            7: "seven",
            8: "eight",
            9: "nine",
        }
        return d[number]


def group_consecutive_years(years: List[int]) -> List[str]:
    """Group consecutive years together and returns a list of formatted year ranges."""
    sorted_years = sorted(years)
    grouped_years = []

    for _, group in groupby(enumerate(sorted_years), lambda ix: ix[0] - ix[1]):
        g = [x[1] for x in group]
        grouped_years.append(f"{g[0]}" if len(g) == 1 else f"{g[0]}-{g[-1]}")

    return grouped_years


def classify_regulation(code_string):
    """Return True if any code in the string is considered regulated."""
    if pd.isna(code_string):
        return False
    for code in str(code_string).split(","):
        code = code.strip()
        try:
            code = str(int(float(code)))  # normalize numeric string like '6.0' to '6'
        except ValueError:
            pass
        if code in REGULATION_MAP:
            return True
    return False
