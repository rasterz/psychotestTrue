from datetime import datetime
from io import BytesIO
import math

import matplotlib
matplotlib.use("Agg")   # обязательно ДО import pyplot

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import CondPageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle,
    KeepTogether
)

from interpretations import types_data

# ----------------------------
# Шрифты
# ----------------------------
pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "fonts/DejaVuSans-Bold.ttf"))

# ----------------------------
# Палитра
# ----------------------------
PRIMARY = HexColor("#1F3A5F")       # тёмно-синий
SECONDARY = HexColor("#3F6EA8")     # акцентный синий
TEXT = HexColor("#1F1F1F")
MUTED = HexColor("#6B7280")
LIGHT_BG = HexColor("#F4F7FB")
BORDER = HexColor("#D7DFEA")


TYPE_COLORS = {
    "R": "#3B82F6",
    "I": "#14B8A6",
    "A": "#8B5CF6",
    "S": "#F59E0B",
    "E": "#EF4444",
    "C": "#64748B",
}

TYPE_COLORS_RL = {
    "R": HexColor("#3B82F6"),
    "I": HexColor("#14B8A6"),
    "A": HexColor("#8B5CF6"),
    "S": HexColor("#F59E0B"),
    "E": HexColor("#EF4444"),
    "C": HexColor("#64748B"),
}

TYPE_LABELS = {
    "R": "Реалистический",
    "I": "Интеллектуальный",
    "A": "Артистический",
    "S": "Социальный",
    "E": "Предпринимательский",
    "C": "Конвенциональный",
}


# ----------------------------
# Вспомогательные функции
# ----------------------------
def sanitize_filename(name: str) -> str:
    bad_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    cleaned = name.strip() if name else "user"
    for ch in bad_chars:
        cleaned = cleaned.replace(ch, "_")
    return cleaned or "user"


def sorted_score_list(scores: dict):
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def get_top_types(scores: dict, n=3):
    return [k for k, _ in sorted_score_list(scores)[:n]]


def get_code_text(code: str) -> str:
    names = [TYPE_LABELS.get(letter, letter) for letter in code]
    return f"{code} — " + " / ".join(names)


def get_interest_levels(scores: dict):
    """
    Делим интересы на 3 группы:
    - ярко выраженные
    - умеренно выраженные
    - менее выраженные
    """
    ordered = sorted_score_list(scores)
    high = [k for k, v in ordered if v >= 10]
    mid = [k for k, v in ordered if 6 <= v <= 9]
    low = [k for k, v in ordered if v <= 5]

    # Чтобы не было пустого блока
    if not high:
        high = [ordered[0][0], ordered[1][0]]
    if not mid:
        mid = [ordered[2][0], ordered[3][0]]
    if not low:
        low = [ordered[-1][0]]

    return high, mid, low


def intelligence_profile_by_code(code: str):
    """
    Условная интерпретация на основе ведущих типов Холланда.
    Это не отдельный тест интеллекта, а ориентировочный профиль.
    """
    base = {
        "R": [("Телесно-кинестетический", 8), ("Натуралистический", 7), ("Пространственный", 6)],
        "I": [("Логико-математический", 9), ("Натуралистический", 7), ("Вербально-аналитический", 6)],
        "A": [("Музыкальный", 8), ("Пространственный", 9), ("Вербально-творческий", 7)],
        "S": [("Межличностный", 9), ("Вербально-коммуникативный", 7), ("Внутриличностный", 6)],
        "E": [("Межличностный", 8), ("Вербально-коммуникативный", 8), ("Внутриличностный", 6)],
        "C": [("Логико-математический", 7), ("Внутриличностный", 6), ("Вербально-аналитический", 6)],
    }

    result = {}
    for letter in code:
        for name, value in base.get(letter, []):
            result[name] = result.get(name, 0) + value

    ordered = sorted(result.items(), key=lambda x: x[1], reverse=True)
    return ordered[:6]


def make_bar_chart(scores: dict):
    letters = ["R", "I", "A", "S", "E", "C"]
    values = [scores.get(x, 0) for x in letters]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bars = ax.bar(letters, values)

    for bar, letter in zip(bars, letters):
        bar.set_color(TYPE_COLORS[letter])

    ax.set_title("Профиль профессиональных интересов RIASEC", fontsize=13)
    ax.set_ylabel("Баллы", fontsize=11)
    ax.set_ylim(0, max(14, max(values) + 2))
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_radar_chart(scores: dict):
    labels = ["R", "I", "A", "S", "E", "C"]
    values = [scores.get(x, 0) for x in labels]
    values += values[:1]

    angles = [n / float(len(labels)) * 2 * math.pi for n in range(len(labels))]
    angles += angles[:1]

    fig = plt.figure(figsize=(6, 6))
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], labels, fontsize=11)
    ax.set_rlabel_position(0)
    plt.yticks([2, 4, 6, 8, 10, 12, 14], ["2", "4", "6", "8", "10", "12", "14"], fontsize=8)
    plt.ylim(0, 14)

    ax.plot(angles, values, linewidth=2.2, color="#1F3A5F")
    ax.fill(angles, values, color="#3F6EA8", alpha=0.22)

    plt.title("Радар-профиль RIASEC", y=1.08, fontsize=13)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_intelligence_chart(intel_data):
    labels = [x[0] for x in intel_data]
    values = [x[1] for x in intel_data]

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    bars = ax.barh(range(len(labels)), values)

    palette = ["#1F3A5F", "#3F6EA8", "#5C85B3", "#7A9CC1", "#96B3CF", "#B5C9DD"]
    for bar, color in zip(bars, palette):
        bar.set_color(color)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_title("Ориентировочный профиль интеллекта", fontsize=13)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontName="DejaVu-Bold",
        fontSize=24,
        leading=30,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        fontName="DejaVu",
        fontSize=11,
        leading=16,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontName="DejaVu-Bold",
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="CardTitle",
        fontName="DejaVu-Bold",
        fontSize=12,
        leading=15,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontName="DejaVu",
        fontSize=10.5,
        leading=15,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="BodySmall",
        fontName="DejaVu",
        fontSize=9.2,
        leading=13,
        textColor=MUTED,
        alignment=TA_LEFT,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="CenterStrong",
        fontName="DejaVu-Bold",
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="CompactBody",
        fontName="DejaVu",
        fontSize=9.4,
        leading=12.2,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="CompactSectionTitle",
        fontName="DejaVu-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceBefore=2,
        spaceAfter=6
    ))

    return styles


def add_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.6)
    canvas.line(2 * cm, height - 1.3 * cm, width - 2 * cm, height - 1.3 * cm)
    canvas.line(2 * cm, 1.2 * cm, width - 2 * cm, 1.2 * cm)

    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 0.75 * cm, "Профориентационный отчёт RIASEC")
    canvas.drawRightString(width - 2 * cm, 0.75 * cm, f"Стр. {doc.page}")
    canvas.restoreState()


def make_info_table(name: str, age: str, contact: str, city: str, category: str, code: str, styles):
    contact_text = contact.strip() if contact else "Не указан"
    city_text = city.strip() if city else "Не указан"
    age_text = str(age).strip() if age else "Не указан"
    category_text = category.strip() if category else "Не указана"

    data = [
        [
            Paragraph("<b>Имя</b>", styles["Body"]),
            Paragraph(name if name else "Не указано", styles["Body"])
        ],
        [
            Paragraph("<b>Возраст</b>", styles["Body"]),
            Paragraph(age_text, styles["Body"])
        ],
        [
            Paragraph("<b>Категория</b>", styles["Body"]),
            Paragraph(category_text, styles["Body"])
        ],
        [
            Paragraph("<b>Способ связи</b>", styles["Body"]),
            Paragraph(contact_text, styles["Body"])
        ],
        [
            Paragraph("<b>Город</b>", styles["Body"]),
            Paragraph(city_text, styles["Body"])
        ],
        [
            Paragraph("<b>Дата прохождения</b>", styles["Body"]),
            Paragraph(datetime.now().strftime("%d.%m.%Y"), styles["Body"])
        ],
        [
            Paragraph("<b>Код Холланда</b>", styles["Body"]),
            Paragraph(code, styles["Body"])
        ],
        [
            Paragraph("<b>Ведущий профиль</b>", styles["Body"]),
            Paragraph(get_code_text(code), styles["Body"])
        ],
    ]

    table = Table(data, colWidths=[5.2 * cm, 10.3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
    ]))
    return table


def make_score_table(scores: dict):
    ordered = sorted_score_list(scores)
    data = [["Тип", "Название", "Баллы", "Краткий комментарий"]]

    max_score = max(scores.values()) if scores else 0

    for letter, value in ordered:
        name = TYPE_LABELS[letter]
        if value >= max_score - 1:
            comment = "Выражено наиболее сильно"
        elif value >= 8:
            comment = "Устойчивый интерес"
        elif value >= 5:
            comment = "Умеренно выражено"
        else:
            comment = "Выражено слабо"

        data.append([letter, name, str(value), comment])

    table = Table(data, colWidths=[1.3 * cm, 5.0 * cm, 2.0 * cm, 7.2 * cm])
    style = TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ])

    for i, (letter, _) in enumerate(ordered, start=1):
        style.add("TEXTCOLOR", (0, i), (0, i), TYPE_COLORS[letter])
        style.add("FONTNAME", (0, i), (0, i), "DejaVu-Bold")

    table.setStyle(style)
    return table


def type_section(letter: str, styles):
    info = types_data[letter]
    title = info["name"]
    text = info["text"]
    fields = info["fields"]

    strengths_map = {
        "R": "Практичность, устойчивость к реальным задачам, интерес к технике, умение работать руками и с конкретным результатом.",
        "I": "Аналитическое мышление, любознательность, склонность к исследованию, способность разбираться в сложных системах.",
        "A": "Креативность, воображение, оригинальность мышления, стремление к самовыражению и созданию нового.",
        "S": "Коммуникативность, эмпатия, готовность поддерживать, обучать и сопровождать других людей.",
        "E": "Инициативность, лидерские качества, умение убеждать, организовывать и вести за собой.",
        "C": "Системность, внимательность, аккуратность, склонность к упорядоченной работе и соблюдению правил.",
    }

    environment_map = {
        "R": "Подходят практико-ориентированные условия труда, конкретные задачи, техника, оборудование, понятный результат работы.",
        "I": "Подходит среда, где нужно исследовать, анализировать, изучать закономерности и решать интеллектуальные задачи.",
        "A": "Подходит свободная, гибкая среда, где приветствуются идеи, нестандартность и творческий подход.",
        "S": "Подходит деятельность, связанная с людьми, обучением, консультированием, сопровождением и поддержкой.",
        "E": "Подходит среда, где есть управление, переговоры, организация процессов и движение к цели.",
        "C": "Подходит структурированная среда, точные инструкции, работа с данными, документами и регламентами.",
    }

    risks_map = {
        "R": "Может утомлять слишком абстрактная, однообразно-теоретическая деятельность без видимого практического результата.",
        "I": "Может утомлять суета, поверхностность, постоянная необходимость быстро продавать идеи без времени на анализ.",
        "A": "Может утомлять жёсткая регламентация, отсутствие свободы, шаблонность и формализм.",
        "S": "Может утомлять изолированная работа без людей и высокая эмоциональная холодность среды.",
        "E": "Может утомлять пассивная, рутинная деятельность без влияния на решения и результат.",
        "C": "Может утомлять хаотичная среда, неопределённость, отсутствие структуры и постоянные резкие изменения.",
    }

    block = []
    block.append(Paragraph(f"{title} тип", styles["CompactSectionTitle"]))
    block.append(Paragraph(text, styles["CompactBody"]))
    block.append(Paragraph(f"<b>Сильные стороны:</b> {strengths_map[letter]}", styles["CompactBody"]))
    block.append(Paragraph(f"<b>Предпочтительная среда:</b> {environment_map[letter]}", styles["CompactBody"]))
    block.append(Paragraph(f"<b>Что может утомлять:</b> {risks_map[letter]}", styles["CompactBody"]))
    block.append(Paragraph(f"<b>Профессиональные интересы:</b> {', '.join(fields)}.", styles["CompactBody"]))

    return block


def interests_block(letters, title, styles):
    names = [TYPE_LABELS[x] for x in letters]
    fields = []
    for x in letters:
        fields.extend(types_data[x]["fields"])
    fields = list(dict.fromkeys(fields))

    content = [
        [Paragraph(f"<b>{title}</b>", styles["CardTitle"])],
        [Paragraph("Типы: " + ", ".join(names), styles["Body"])],
        [Paragraph("Направления: " + ", ".join(fields), styles["Body"])],
    ]

    table = Table(content, colWidths=[16.0 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


# ----------------------------
# Основная функция
# ----------------------------
def create_pdf(name, age, contact, city, category, scores, code):
    safe_name = sanitize_filename(name)
    filename = f"result_{safe_name}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.8 * cm
    )

    styles = create_styles()
    story = []

    top3 = get_top_types(scores, 3)
    high, mid, low = get_interest_levels(scores)
    intel_profile = intelligence_profile_by_code(code)

    # ----------------------------
    # 1. Обложка
    # ----------------------------
    story.append(Spacer(1, 2.0 * cm))
    story.append(Paragraph("ПРОФОРИЕНТАЦИОННЫЙ ОТЧЁТ", styles["ReportTitle"]))
    story.append(Paragraph("Методика профессиональных интересов по типологии RIASEC", styles["ReportSubtitle"]))
    story.append(Spacer(1, 1.0 * cm))
    story.append(make_info_table(name, age, contact, city, category, code, styles))
    story.append(Spacer(1, 1.0 * cm))

    summary_text = (
        f"По итогам тестирования респондента "
        f"<b>{name}</b> наиболее выраженным является профиль <b>{get_code_text(code)}</b>. "
        f"Категория прохождения теста: <b>{category}</b>. "
        f"Это означает, что в наибольшей степени проявляются интересы, связанные "
        f"с видами деятельности, соответствующими ведущим типам личности по Холланду. "
        f"Данный отчёт показывает не только количественные результаты, но и их "
        f"практическую интерпретацию: профессиональные склонности, возможные интересы, "
        f"ориентировочный профиль интеллекта и направления дальнейшего развития."
    )
    story.append(Paragraph(summary_text, styles["Body"]))
    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph("Документ подготовлен автоматически на основе ответов пользователя", styles["ReportSubtitle"]))
    story.append(PageBreak())

    # ----------------------------
    # 2. Итоговая интерпретация
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("1. Итоговый профиль", styles["SectionTitle"]))
    story.append(Paragraph(
        f"Ведущий код личности: <b>{code}</b>. "
        f"Наиболее значимыми являются следующие типы: "
        f"<b>{TYPE_LABELS[top3[0]]}</b>, <b>{TYPE_LABELS[top3[1]]}</b> и <b>{TYPE_LABELS[top3[2]]}</b>.",
        styles["Body"]
    ))

    story.append(make_score_table(scores))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Интерпретация результатов должна рассматриваться как ориентир для выбора профессиональных сфер, "
        "а не как окончательный диагноз. Наиболее полезно сопоставлять результаты отчёта с реальными "
        "интересами, школьными предметами, особенностями мотивации и опытом выполнения разных задач.",
        styles["BodySmall"]
    ))

    story.append(PageBreak())

    # ----------------------------
    # 3. Столбчатая диаграмма
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("2. Визуальный профиль RIASEC", styles["SectionTitle"]))
    story.append(Paragraph(
        "Ниже представлен визуальный профиль профессиональных интересов по шести шкалам RIASEC.",
        styles["Body"]
    ))

    bar_img = Image(make_bar_chart(scores), width=16.0 * cm, height=8.5 * cm)
    story.append(bar_img)
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "Столбчатая диаграмма показывает выраженность каждого из шести типов интересов.",
        styles["BodySmall"]
    ))
    story.append(PageBreak())

    # ----------------------------
    # 3.1. Радар-диаграмма
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("3. Радар-профиль", styles["SectionTitle"]))

    radar_img = Image(make_radar_chart(scores), width=12.0 * cm, height=12.0 * cm)
    story.append(radar_img)
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "Радар-профиль помогает увидеть общую конфигурацию профессиональных склонностей: "
        "насколько они сосредоточены вокруг 1–2 направлений или распределены более широко.",
        styles["BodySmall"]
    ))
    story.append(PageBreak())

    # ----------------------------
    # 4. Разбор ведущих типов
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("3. Подробный разбор ведущих типов личности", styles["SectionTitle"]))
    for letter in top3:
        story.extend(type_section(letter, styles))
        story.append(Spacer(1, 0.2 * cm))
        # тут маленький текст изменялся из-за ["CompactBody"]

    story.append(PageBreak())

    # ----------------------------
    # 5. Профессиональные интересы
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("4. Профессиональные интересы", styles["SectionTitle"]))
    story.append(Paragraph(
        "Ниже показано, какие направления интересов можно считать ярко выраженными, "
        "умеренно выраженными и менее выраженными по итогам тестирования.",
        styles["Body"]
    ))

    story.append(interests_block(high, "Ярко выраженные интересы", styles))
    story.append(Spacer(1, 0.35 * cm))
    story.append(interests_block(mid, "Умеренно выраженные интересы", styles))
    story.append(Spacer(1, 0.35 * cm))
    story.append(interests_block(low, "Менее выраженные интересы", styles))
    story.append(PageBreak())

    # ----------------------------
    # 6. Профиль интеллекта
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("5. Ориентировочный профиль интеллекта", styles["SectionTitle"]))
    story.append(Paragraph(
        "Этот раздел не является самостоятельной психометрической диагностикой интеллекта. "
        "Он представляет собой интерпретационный профиль, построенный на основе ведущих "
        "интересов и типов активности, проявленных в тесте.",
        styles["Body"]
    ))

    intel_img = Image(make_intelligence_chart(intel_profile), width=16.0 * cm, height=9.2 * cm)
    story.append(intel_img)
    story.append(Spacer(1, 0.4 * cm))

    for name_i, value_i in intel_profile[:3]:
        story.append(Paragraph(
            f"<b>{name_i}</b> — ориентировочно выражен на высоком уровне в сравнении с другими профилями данного отчёта.",
            styles["Body"]
        ))

    story.append(PageBreak())

    # ----------------------------
    # 7. Рекомендации
    # ----------------------------
    story.append(CondPageBreak(4 * cm))
    story.append(Paragraph("6. Практические рекомендации", styles["SectionTitle"]))

    recommended_fields = []
    for letter in top3:
        recommended_fields.extend(types_data[letter]["fields"])
    recommended_fields = list(dict.fromkeys(recommended_fields))

    rec_text_1 = (
        "При выборе профессии и направления обучения рекомендуется в первую очередь учитывать "
        "ведущие типы интересов, а также те учебные предметы и виды задач, которые вызывают "
        "устойчивый интерес, а не только ситуативную симпатию."
    )
    rec_text_2 = (
        f"На основании результатов теста целесообразно обратить внимание на следующие направления: "
        f"<b>{', '.join(recommended_fields)}</b>."
    )
    rec_text_3 = (
        "Полезно дополнительно проверить себя через практику: профпробы, кружки, проектную деятельность, "
        "общение со специалистами, пробные задания, элективные курсы и открытые образовательные программы."
    )
    rec_text_4 = (
        "Если выбор профессии вызывает сомнения, имеет смысл сочетать данный отчёт "
        "с дополнительной диагностикой способностей, ценностей, школьной успеваемости и мотивации."
    )

    story.append(Paragraph(rec_text_1, styles["Body"]))
    story.append(Paragraph(rec_text_2, styles["Body"]))
    story.append(Paragraph(rec_text_3, styles["Body"]))
    story.append(Paragraph(rec_text_4, styles["Body"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Краткий вывод", styles["SectionTitle"]))
    story.append(Paragraph(
        f"Профиль <b>{code}</b> указывает на то, что выбор профессионального пути будет наиболее успешным "
        f"в тех сферах, где человек сможет реализовать качества, свойственные типам "
        f"<b>{TYPE_LABELS[top3[0]]}</b>, <b>{TYPE_LABELS[top3[1]]}</b> и <b>{TYPE_LABELS[top3[2]]}</b>. "
        f"Именно сочетание этих особенностей является ключом к дальнейшему развитию и профессиональному самоопределению.",
        styles["Body"]
    ))

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return filename