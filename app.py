from flask import Flask, render_template, request, jsonify, session
from questions import questions, questions_part2, interest_questions_teen, interest_scales, interest_questions_adult, interest_scales_adult
from scoring import calculate_riasec, calculate_pairs_riasec, calculate_interest_map, calculate_interest_map_adult
from pdf_report import create_pdf
from telegram_sender import send_pdf_to_telegram
from telegram_sender import send_consultation_to_telegram

app = Flask(__name__)
app.secret_key = "riasec_secret_key"


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/test")
def index():
    return render_template("test.html", questions=questions)


@app.route("/test2", methods=["POST"])
def test2():
    # Сохраняем ответы первой методики
    answers_part1 = []
    for i in range(len(questions)):
        ans = request.form.get(f"q{i}")
        answers_part1.append(ans)

    session["answers_part1"] = answers_part1

    # Сохраняем данные пользователя

    session["name"] = request.form.get("name")

    age_raw = request.form.get("age")
    session["age"] = age_raw

    session["contact"] = request.form.get("contact")
    session["city"] = request.form.get("city")

    try:
        age_number = int(age_raw)
    except (TypeError, ValueError):
        age_number = 0

    session["category"] = "Подросток" if age_number < 18 else "Взрослый"

    return render_template(
        "test2.html",
        questions=questions_part2,
        name=session.get("name", ""),
        age=session.get("age", ""),
        contact=session.get("contact", ""),
        city=session.get("city", ""),
        category=session.get("category", "")
    )


@app.route("/test3", methods=["POST"])
def test3():

    # собираем ответы второго теста (парного Холланда)
    answers_part2 = []

    for i in range(len(questions_part2)):
        ans = request.form.get(f"q{i}")
        answers_part2.append(ans)

    # сохраняем в session
    session["answers_part2"] = answers_part2

    if session.get("category") != "Подросток":
        return render_template(
            "test3.html",
            questions=interest_questions_adult,
            name=session.get("name", ""),
            age=session.get("age", ""),
            contact=session.get("contact", ""),
            city=session.get("city", ""),
            category=session.get("category", "")
        )

    # если подросток — показываем карту интересов
    return render_template(
        "test3.html",
        questions=interest_questions_teen,
        name=session.get("name",""),
        age=session.get("age",""),
        contact=session.get("contact",""),
        city=session.get("city",""),
        category=session.get("category","")
    )


@app.route("/result", methods=["POST"])
def result():
    name = session.get("name", request.form.get("name"))
    age = session.get("age", request.form.get("age"))
    contact = session.get("contact", request.form.get("contact"))
    city = session.get("city", request.form.get("city"))
    category = session.get("category", request.form.get("category"))

    # 1. Берём уже сохранённые ответы test1 и test2
    answers_part1 = session.get("answers_part1", [])
    answers_part2 = session.get("answers_part2", [])

    # 2. Считаем Холланд по первой методике
    scores_part1 = calculate_riasec(answers_part1)

    # 3. Считаем Холланд по парному тесту
    scores_part2 = calculate_pairs_riasec(answers_part2)

    # 4. Складываем результаты двух методик
    scores = {}
    for key in scores_part1.keys():
        scores[key] = scores_part1[key] + scores_part2[key]

    # 5. Строим итоговый код Холланда
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    code = "".join([item[0] for item in sorted_scores[:3]])

    # 6. Считываем test3 для подростка и взрослого
    interest_results = []

    interest_answers = []
    for i in range(60):
        value = request.form.get(f"iq{i}")
        interest_answers.append(int(value) if value is not None else 3)

    if category == "Подросток":
        raw_interest_results = calculate_interest_map(interest_answers)
        current_interest_scales = interest_scales
    else:
        raw_interest_results = calculate_interest_map_adult(interest_answers)
        current_interest_scales = interest_scales_adult

    # Привязываем названия шкал
    for item in raw_interest_results:
        interest_results.append({
            "name": current_interest_scales[item["scale"]],
            "score": item["score"],
            "level": item["level"]
        })

    # сортировка по убыванию
    interest_results.sort(key=lambda x: x["score"], reverse=True)

    pdf_file = create_pdf(
        name=name,
        age=age,
        contact=contact,
        city=city,
        category=category,
        scores=scores,
        code=code,
        interest_results=interest_results
    )

    caption = (
        f"Новый отчет по тесту RIASEC\n"
        f"Имя: {name}\n"
        f"Возраст: {age}\n"
        f"Категория: {category}\n"
        f"Контакт: {contact if contact else 'не указан'}\n"
        f"Город: {city if city else 'не указан'}\n"
        f"Код Холланда: {code}"
    )

    try:
        send_pdf_to_telegram(pdf_file, caption)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

    return render_template(
        "result.html",
        scores=scores,
        code=code,
        pdf_file=pdf_file,
        name=name,
        age=age,
        contact=contact,
        city=city,
        category=category,
        interest_results=interest_results
    )


@app.route("/send-consultation-request", methods=["POST"])
def send_consultation_request():
    try:
        data = request.get_json()

        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()
        contact_method = (data.get("contact_method") or "").strip()
        contact_value = (data.get("contact_value") or "").strip()
        message = (data.get("message") or "").strip()

        allowed_methods = {"telegram", "max", "vk", "phone"}

        if not first_name:
            return jsonify({"ok": False, "error": "Укажите имя"}), 400

        if not last_name:
            return jsonify({"ok": False, "error": "Укажите фамилию"}), 400

        if contact_method not in allowed_methods:
            return jsonify({"ok": False, "error": "Некорректный способ связи"}), 400

        if not contact_value:
            return jsonify({"ok": False, "error": "Укажите контактные данные"}), 400

        send_consultation_to_telegram(
            first_name=first_name,
            last_name=last_name,
            contact_method=contact_method,
            contact_value=contact_value,
            message=message
        )

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)