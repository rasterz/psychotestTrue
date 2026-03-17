types = ["R", "I", "A", "S", "E", "C"]


def calculate_riasec(answers):
    scores = {t: 0 for t in types}

    for i, answer in enumerate(answers):
        if answer == "Да":
            t = types[i % 6]
            scores[t] += 1

    return scores


def calculate_pairs_riasec(pair_answers):
    scores = {t: 0 for t in types}

    from questions import questions_part2

    for i, answer in enumerate(pair_answers):
        pair = questions_part2[i]

        if answer == "A":
            scores[pair["left_type"]] += 1
        elif answer == "B":
            scores[pair["right_type"]] += 1

    return scores


def calculate_interest_map(answers):
    results = []

    for i in range(20):
        score = answers[i] + answers[i + 20] + answers[i + 40]

        if score >= 9:
            level = "Высокий интерес"
        elif score >= 7:
            level = "Средний интерес"
        else:
            level = "Слабый интерес"

        results.append({
            "scale": i,
            "score": score,
            "level": level
        })

    return results


def calculate_interest_map_adult(answers):
    results = []

    for i in range(20):
        score = answers[i] + answers[i + 20] + answers[i + 40]

        if score >= 9:
            level = "Высокий интерес"
        elif score >= 7:
            level = "Средний интерес"
        else:
            level = "Слабый интерес"

        results.append({
            "scale": i,
            "score": score,
            "level": level
        })

    return results