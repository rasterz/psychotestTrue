from flask import Flask, render_template, request, jsonify, session, abort, redirect, url_for
from questions import questions, questions_part2, interest_questions_teen, interest_scales, interest_questions_adult, interest_scales_adult
from scoring import calculate_riasec, calculate_pairs_riasec, calculate_interest_map, calculate_interest_map_adult
from pdf_report import create_pdf
from telegram_sender import send_pdf_to_telegram
from telegram_sender import send_consultation_to_telegram
import sqlite3
import json
from functools import wraps
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font
from flask import send_file
import random


app = Flask(__name__)
app.secret_key = "riasec_secret_key"

DATABASE = "crm.db"
CRM_LOGIN = "ilyasova"
CRM_PASSWORD = "crm2000ilyasova"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        first_name TEXT,
        last_name TEXT,
        full_name TEXT,

        age TEXT,
        city TEXT,

        contact_method TEXT,
        contact_value TEXT,

        category TEXT,
        holland_code TEXT,

        request_message TEXT,
        scores_json TEXT,
        interest_results_json TEXT,

        consent_given INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lead_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        note_text TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
    )
    """)

    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN status TEXT DEFAULT 'new'")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN note TEXT")
    except:
        pass

    conn.commit()
    conn.close()


def save_lead(
    source,
    first_name=None,
    last_name=None,
    full_name=None,
    age=None,
    city=None,
    contact_method=None,
    contact_value=None,
    category=None,
    holland_code=None,
    request_message=None,
    scores=None,
    interest_results=None,
    consent_given=0
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO leads (
        source,
        first_name,
        last_name,
        full_name,
        age,
        city,
        contact_method,
        contact_value,
        category,
        holland_code,
        request_message,
        scores_json,
        interest_results_json,
        consent_given
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        source,
        first_name,
        last_name,
        full_name,
        age,
        city,
        contact_method,
        contact_value,
        category,
        holland_code,
        request_message,
        json.dumps(scores, ensure_ascii=False) if scores else None,
        json.dumps(interest_results, ensure_ascii=False) if interest_results else None,
        consent_given
    ))

    conn.commit()
    conn.close()

def crm_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("crm_logged_in"):
            return redirect(url_for("crm_login"))
        return view_func(*args, **kwargs)
    return wrapped_view

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/brain-preview")
def brain_preview():
    secret = request.args.get("key")
    if secret != "tvoy-sekretnyy-klyuch-2026":
        abort(404)
    return render_template("brain-preview.html")

@app.route("/test")
def index():
    return render_template("test.html", questions=questions)


@app.route("/test2", methods=["POST"])
def test2():
    privacy_consent = request.form.get("privacy_consent")

    if privacy_consent != "1":
        return "Нужно подтвердить согласие с политикой обработки персональных данных", 400

    session["privacy_consent"] = 1
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

    try:
        save_lead(
            source="test",
            first_name=name,
            full_name=name,
            age=age,
            city=city,
            contact_method="unknown",
            contact_value=contact,
            category=category,
            holland_code=code,
            scores=scores,
            interest_results=interest_results,
            consent_given=session.get("privacy_consent", 0)
        )
    except Exception as e:
        print("Ошибка сохранения лида в CRM:", e)

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
        privacy_consent = data.get("privacy_consent")

        allowed_methods = {"telegram", "max", "vk", "phone"}

        if not first_name:
            return jsonify({"ok": False, "error": "Укажите имя"}), 400

        if not last_name:
            return jsonify({"ok": False, "error": "Укажите фамилию"}), 400

        if contact_method not in allowed_methods:
            return jsonify({"ok": False, "error": "Некорректный способ связи"}), 400

        if not contact_value:
            return jsonify({"ok": False, "error": "Укажите контактные данные"}), 400

        if privacy_consent is not True:
            return jsonify({
                "ok": False,
                "error": "Нужно подтвердить согласие с политикой обработки персональных данных"
            }), 400

        send_consultation_to_telegram(
            first_name=first_name,
            last_name=last_name,
            contact_method=contact_method,
            contact_value=contact_value,
            message=message
        )

        save_lead(
            source="consultation",
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}".strip(),
            contact_method=contact_method,
            contact_value=contact_value,
            request_message=message,
            consent_given=1 if privacy_consent else 0
        )

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/debug-test-result")
def debug_test_result():
    first_names = [
        "Максим", "Алина", "София", "Илья", "Мария", "Егор", "Анна",
        "Даниил", "Виктория", "Никита", "Полина", "Артём", "Ева"
    ]

    last_names = [
        "Иванов", "Петрова", "Смирнов", "Карапетян", "Саркисян",
        "Попов", "Васильева", "Мкртчян", "Григорян", "Кузнецова"
    ]

    cities = [
        "Ереван", "Абовян", "Гюмри", "Ванадзор", "Раздан",
        "Москва", "Санкт-Петербург", "Казань", "Краснодар", "Тбилиси"
    ]

    contact_prefixes = [
        "career", "future", "study", "choice", "profi",
        "testuser", "riasec", "mentor", "focus", "vector"
    ]

    personas = [
        {"code": "RIA", "fav": {"R", "I", "A"}, "age_range": (14, 22)},
        {"code": "IAS", "fav": {"I", "A", "S"}, "age_range": (14, 24)},
        {"code": "SEC", "fav": {"S", "E", "C"}, "age_range": (15, 30)},
        {"code": "IRC", "fav": {"I", "R", "C"}, "age_range": (14, 28)},
        {"code": "AES", "fav": {"A", "E", "S"}, "age_range": (14, 26)},
        {"code": "CRE", "fav": {"C", "R", "E"}, "age_range": (16, 32)},
    ]

    # Порядок первого теста у тебя идет по кругу R I A S E C
    cycle_types = ["R", "I", "A", "S", "E", "C"]

    persona = random.choice(personas)

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    full_name = f"{first_name} {last_name}"

    age_number = random.randint(*persona["age_range"])
    city = random.choice(cities)
    contact = f"@{random.choice(contact_prefixes)}_{random.randint(100, 999)}"

    session["name"] = full_name
    session["age"] = str(age_number)
    session["contact"] = contact
    session["city"] = city
    session["category"] = "Подросток" if age_number < 18 else "Взрослый"
    session["privacy_consent"] = 1

    # -------- 1 тест --------
    # В любимые типы чаще отвечает "Да", в остальные чаще "Нет"
    answers_part1 = []
    for i, _ in enumerate(questions):
        q_type = cycle_types[i % 6]

        if q_type in persona["fav"]:
            answer = random.choices(["Да", "Нет"], weights=[78, 22])[0]
        else:
            answer = random.choices(["Да", "Нет"], weights=[30, 70])[0]

        answers_part1.append(answer)

    session["answers_part1"] = answers_part1

    # -------- 2 тест --------
    # Выбираем левый или правый вариант с уклоном в любимые типы
    answers_part2 = []
    for pair in questions_part2:
        left_type = pair.get("left_type")
        right_type = pair.get("right_type")

        left_score = 1
        right_score = 1

        if left_type in persona["fav"]:
            left_score += 3
        if right_type in persona["fav"]:
            right_score += 3

        choice = random.choices(
            ["A", "B"],
            weights=[left_score, right_score]
        )[0]

        answers_part2.append(choice)

    session["answers_part2"] = answers_part2

    # -------- 3 тест интересов --------
    # Делаем живой разброс, а не голые случайные единицы
    interest_values = []
    for _ in range(60):
        interest_values.append(str(random.choices(
            [1, 2, 3, 4, 5],
            weights=[8, 14, 26, 30, 22]
        )[0]))

    interest_inputs = "\n".join(
        f'<input type="hidden" name="iq{i}" value="{interest_values[i]}">'
        for i in range(60)
    )

    return f"""
    <html>
      <body>
        <form id="debugForm" method="POST" action="/result">
          {interest_inputs}
        </form>
        <script>
          document.getElementById('debugForm').submit();
        </script>
      </body>
    </html>
    """

@app.route("/debug-consultation")
def debug_consultation():
    first_names = [
        "Максим", "Алина", "София", "Илья", "Мария", "Егор", "Анна",
        "Даниил", "Виктория", "Никита", "Полина", "Артём", "Ева"
    ]

    last_names = [
        "Иванов", "Петрова", "Смирнов", "Карапетян", "Саркисян",
        "Попов", "Васильева", "Мкртчян", "Григорян", "Кузнецова"
    ]

    messages = [
        "Хочу понять, какая профессия мне действительно подходит.",
        "Не могу выбрать между дизайном, психологией и маркетингом.",
        "Нужна консультация по выбору профессии после 11 класса.",
        "Хочу разобраться, в какой сфере у меня больше шансов раскрыться.",
        "Сомневаюсь между техническим и гуманитарным направлением.",
        "Ребёнок не понимает, куда поступать, нужна помощь.",
        "Хочется понять свои сильные стороны и подходящую профессию.",
        "Интересно, стоит ли идти в IT или лучше рассмотреть другое направление.",
        "Нужна консультация по профориентации для подростка.",
        "Хочу выбрать профессию осознанно, а не наугад.",
        "Есть интерес к творческим профессиям, но боюсь ошибиться.",
        "Нужна помощь в выборе карьерного направления."
    ]

    telegram_prefixes = ["career", "future", "choice", "mentor", "vector", "focus"]
    vk_prefixes = ["id", "career", "vector", "choice", "user"]
    max_prefixes = ["maxcareer", "maxuser", "careermax", "focusmax"]
    phone_prefixes = ["+7999", "+7985", "+7912", "+37493", "+37494"]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    contact_method = random.choice(["telegram", "vk", "max", "phone"])
    message = random.choice(messages)

    if contact_method == "telegram":
        contact_value = f"@{random.choice(telegram_prefixes)}_{random.randint(100, 999)}"
    elif contact_method == "vk":
        prefix = random.choice(vk_prefixes)
        if prefix == "id":
            contact_value = f"id{random.randint(100000, 999999)}"
        else:
            contact_value = f"{prefix}_{random.randint(100, 999)}"
    elif contact_method == "max":
        contact_value = f"@{random.choice(max_prefixes)}_{random.randint(100, 999)}"
    else:
        contact_value = f"{random.choice(phone_prefixes)}{random.randint(1000000, 9999999)}"

    try:
        save_lead(
            source="consultation",
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}".strip(),
            contact_method=contact_method,
            contact_value=contact_value,
            request_message=message,
            consent_given=1
        )
    except Exception as e:
        return f"Ошибка сохранения тестовой консультации: {e}", 500

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 24px;">
        <h2>Тестовая консультация создана</h2>
        <p><strong>Имя:</strong> {first_name} {last_name}</p>
        <p><strong>Способ связи:</strong> {contact_method}</p>
        <p><strong>Контакт:</strong> {contact_value}</p>
        <p><strong>Сообщение:</strong> {message}</p>
        <p><a href="/crm">Открыть CRM</a></p>
      </body>
    </html>
    """

@app.route("/crm-login", methods=["GET", "POST"])
def crm_login():
    error = None

    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()

        if login == CRM_LOGIN and password == CRM_PASSWORD:
            session["crm_logged_in"] = True
            return redirect(url_for("crm_panel"))
        else:
            error = "Неверный логин или пароль"

    return render_template("crm_login.html", error=error)



@app.route("/crm")
@crm_login_required
def crm_panel():

    conn = get_db_connection()
    leads = conn.execute("""
        SELECT *
        FROM leads
        ORDER BY created_at DESC, id DESC
    """).fetchall()

    parsed_leads = []

    for lead in leads:
        lead = dict(lead)

        if lead["scores_json"]:
            lead["scores"] = json.loads(lead["scores_json"])
        else:
            lead["scores"] = None

        if lead["interest_results_json"]:
            lead["interests"] = json.loads(lead["interest_results_json"])
        else:
            lead["interests"] = None

        notes = conn.execute("""
            SELECT id, note_text, created_at
            FROM lead_notes
            WHERE lead_id = ?
            ORDER BY id DESC
        """, (lead["id"],)).fetchall()

        lead["notes"] = [dict(note) for note in notes]

        parsed_leads.append(lead)

    conn.close()

    return render_template("crm.html", leads=parsed_leads)

@app.route("/crm-add-note", methods=["POST"])
@crm_login_required
def crm_add_note():
    data = request.get_json()

    lead_id = data.get("lead_id")
    note = (data.get("note") or "").strip()

    if not lead_id:
        return jsonify({"ok": False, "error": "Не передан ID заявки"}), 400

    if not note:
        return jsonify({"ok": False, "error": "Пустую заметку нельзя сохранить"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lead_notes (lead_id, note_text)
        VALUES (?, ?)
    """, (lead_id, note))
    note_id = cursor.lastrowid

    new_note = conn.execute("""
        SELECT id, note_text, created_at
        FROM lead_notes
        WHERE id = ?
    """, (note_id,)).fetchone()

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "note": dict(new_note)
    })

@app.route("/crm-delete-note", methods=["POST"])
@crm_login_required
def crm_delete_note():
    data = request.get_json()

    note_id = data.get("note_id")

    if not note_id:
        return jsonify({"ok": False, "error": "Не передан ID заметки"}), 400

    conn = get_db_connection()
    conn.execute("DELETE FROM lead_notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/crm-delete-lead", methods=["POST"])
@crm_login_required
def crm_delete_lead():
    data = request.get_json()
    lead_id = data.get("lead_id")

    if not lead_id:
        return jsonify({"ok": False, "error": "Не передан ID заявки"}), 400

    conn = get_db_connection()

    lead = conn.execute(
        "SELECT id, status FROM leads WHERE id = ?",
        (lead_id,)
    ).fetchone()

    if not lead:
        conn.close()
        return jsonify({"ok": False, "error": "Заявка не найдена"}), 404

    if (lead["status"] or "new") != "archive":
        conn.close()
        return jsonify({"ok": False, "error": "Удалять навсегда можно только из архива"}), 400

    conn.execute("DELETE FROM lead_notes WHERE lead_id = ?", (lead_id,))
    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/crm-update-status", methods=["POST"])
@crm_login_required
def crm_update_status():
    data = request.get_json()

    lead_id = data.get("lead_id")
    status = (data.get("status") or "").strip()

    allowed_statuses = {"new", "in_progress", "consultation", "done", "archive"}

    if not lead_id:
        return jsonify({"ok": False, "error": "Не передан ID заявки"}), 400

    if status not in allowed_statuses:
        return jsonify({"ok": False, "error": "Некорректный статус"}), 400

    conn = get_db_connection()
    conn.execute(
        "UPDATE leads SET status = ? WHERE id = ?",
        (status, lead_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/crm-update-field", methods=["POST"])
@crm_login_required
def crm_update_field():
    data = request.get_json()

    lead_id = data.get("lead_id")
    field = (data.get("field") or "").strip()
    value = data.get("value")

    allowed_fields = {
        "full_name",
        "contact_value",
        "contact_method",
        "age",
        "city",
        "category",
        "request_message"
    }

    allowed_contact_methods = {"telegram", "max", "vk", "phone", "unknown", ""}
    allowed_categories = {"Подросток", "Взрослый", "", None}

    if not lead_id:
        return jsonify({"ok": False, "error": "Не передан ID заявки"}), 400

    if field not in allowed_fields:
        return jsonify({"ok": False, "error": "Это поле нельзя редактировать"}), 400

    if value is None:
        value = ""
    value = str(value).strip()

    if field == "contact_method" and value not in allowed_contact_methods:
        return jsonify({"ok": False, "error": "Некорректный способ связи"}), 400

    if field == "category" and value not in allowed_categories:
        return jsonify({"ok": False, "error": "Некорректная категория"}), 400

    conn = get_db_connection()
    conn.execute(
        f"UPDATE leads SET {field} = ? WHERE id = ?",
        (value, lead_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "field": field,
        "value": value
    })

@app.route("/crm-update-note", methods=["POST"])
@crm_login_required
def crm_update_note():
    data = request.get_json()

    lead_id = data.get("lead_id")
    note = (data.get("note") or "").strip()

    if not lead_id:
        return jsonify({"ok": False, "error": "Не передан ID заявки"}), 400

    conn = get_db_connection()
    conn.execute(
        "UPDATE leads SET note = ? WHERE id = ?",
        (note, lead_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/crm-export")
@crm_login_required
def crm_export():
    conn = get_db_connection()
    leads = conn.execute("""
        SELECT *
        FROM leads
        WHERE COALESCE(status, 'new') != 'archive'
        ORDER BY created_at DESC, id DESC
    """).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "CRM"

    headers = [
        "Дата",
        "Источник",
        "Имя",
        "Фамилия",
        "Полное имя",
        "Контакт",
        "Способ связи",
        "Возраст",
        "Город",
        "Категория",
        "Код Холланда",
        "Согласие",
        "Баллы Холланда",
        "Топ интересов",
        "Сообщение"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for lead in leads:
        scores_text = ""
        interests_text = ""

        if lead["scores_json"]:
            try:
                scores = json.loads(lead["scores_json"])
                scores_text = ", ".join(f"{k}: {v}" for k, v in scores.items())
            except Exception:
                scores_text = lead["scores_json"]

        if lead["interest_results_json"]:
            try:
                interests = json.loads(lead["interest_results_json"])
                interests_text = "; ".join(
                    f'{item.get("name", "")} ({item.get("score", "")}, {item.get("level", "")})'
                    for item in interests[:10]
                )
            except Exception:
                interests_text = lead["interest_results_json"]

        ws.append([
            lead["created_at"] or "",
            "Тест" if lead["source"] == "test" else "Консультация",
            lead["first_name"] or "",
            lead["last_name"] or "",
            lead["full_name"] or "",
            lead["contact_value"] or "",
            lead["contact_method"] or "",
            lead["age"] or "",
            lead["city"] or "",
            lead["category"] or "",
            lead["holland_code"] or "",
            "Да" if lead["consent_given"] else "Нет",
            scores_text,
            interests_text,
            lead["request_message"] or ""
        ])

    column_widths = {
        "A": 20,
        "B": 16,
        "C": 18,
        "D": 18,
        "E": 24,
        "F": 24,
        "G": 18,
        "H": 10,
        "I": 18,
        "J": 16,
        "K": 14,
        "L": 12,
        "M": 28,
        "N": 48,
        "O": 40,
    }

    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="crm_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/crm-logout")
def crm_logout():
    session.pop("crm_logged_in", None)
    return redirect(url_for("crm_login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=True)