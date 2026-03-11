types = ["R", "I", "A", "S", "E", "C"]

def calculate_riasec(answers):

    scores = {
        "R":0,
        "I":0,
        "A":0,
        "S":0,
        "E":0,
        "C":0
    }

    for i, answer in enumerate(answers):

        if answer == "yes":

            t = types[i % 6]
            scores[t] += 1

    return scores