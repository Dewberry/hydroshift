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
