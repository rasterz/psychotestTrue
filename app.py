from flask import Flask, render_template, request
from questions import questions
from scoring import calculate_riasec
from pdf_report import create_pdf
from telegram_sender import send_pdf_to_telegram

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("test.html", questions=questions)


@app.route("/result", methods=["POST"])
def result():
    name = request.form.get("name")
    age = request.form.get("age")
    contact = request.form.get("contact")
    city = request.form.get("city")
    category = request.form.get("category")
    answers = []
    for i in range(len(questions)):
        ans = request.form.get(f"q{i}")
        answers.append(ans)

    scores = calculate_riasec(answers)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    code = "".join([item[0] for item in sorted_scores[:3]])

    pdf_file = create_pdf(
        name=name,
        age=age,
        contact=contact,
        city=city,
        category=category,
        scores=scores,
        code=code
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
        category=category
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)