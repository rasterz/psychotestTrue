from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle,
    KeepTogether,
    CondPageBreak,
    KeepInFrame,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from interpretations import types_data


# ----------------------------
# Шрифты
# ----------------------------
pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "fonts/DejaVuSans-Bold.ttf"))


# ----------------------------
# Палитра
# ----------------------------
PRIMARY = HexColor("#1F4B43")       # тёмный изумруд
PRIMARY_SOFT = HexColor("#2E6B60")
ACCENT = HexColor("#D8A94D")        # тёплый золотистый акцент
TEXT = HexColor("#1D2430")
MUTED = HexColor("#667085")
LINE = HexColor("#D9E4E1")
LIGHT_BG = HexColor("#F5F9F8")
CARD_BG = HexColor("#EEF5F3")
WHITE = colors.white

TYPE_COLORS = {
    "R": "#4C956C",
    "I": "#2A9D8F",
    "A": "#9B5DE5",
    "S": "#F4A261",
    "E": "#E76F51",
    "C": "#577590",
}

TYPE_COLORS_RL = {k: HexColor(v) for k, v in TYPE_COLORS.items()}

TYPE_LABELS = {
    "R": "Реалистический",
    "I": "Исследовательский",
    "A": "Артистический",
    "S": "Социальный",
    "E": "Предпринимательский",
    "C": "Конвенциональный",
}

TYPE_CARD_TITLES = {
    "R": "Реалистический",
    "I": "Исследовательский",
    "A": "Артистический",
    "S": "Социальный",
    "E": "Предприниматель-\nский",
    "C": "Конвенциональный",
}

TYPE_SHORT = {
    "R": "Практика и результат",
    "I": "Анализ и исследование",
    "A": "Творчество и идеи",
    "S": "Люди и поддержка",
    "E": "Влияние и организация",
    "C": "Порядок и точность",
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


def build_recommended_fields(top_letters):
    fields = []
    for letter in top_letters:
        fields.extend(types_data.get(letter, {}).get("fields", []))
    result = []
    for item in fields:
        if item not in result:
            result.append(item)
    return result[:10]


def get_display_name(name: str) -> str:
    return name.strip() if name and name.strip() else "Участник тестирования"


def build_interest_groups(interest_results):
    high = [x for x in interest_results if x["level"] == "Высокий интерес"]
    mid = [x for x in interest_results if x["level"] == "Средний интерес"]
    low = [x for x in interest_results if x["level"] == "Слабый интерес"]
    return high, mid, low


def build_interest_summary(category: str, interest_results):
    top = interest_results[:5]
    names = [x["name"] for x in top]

    if not names:
        return (
            "По третьей методике выраженных пиков не выявлено. "
            "Это может означать широкий круг интересов или осторожный стиль ответов."
        )

    if category == "Подросток":
        return (
            "Сильнее всего откликаются направления: "
            f"<b>{', '.join(names)}</b>. "
            "Их полезно учитывать при выборе профиля обучения, кружков, проектной деятельности "
            "и первых профессиональных проб."
        )

    return (
        "Сильнее всего откликаются направления: "
        f"<b>{', '.join(names)}</b>. "
        "Их стоит рассматривать как опорные точки для профессионального развития, "
        "уточнения специализации или смены карьерного вектора."
    )


def strengths_map():
    return {
        "R": "Практичность, устойчивость к реальным задачам, интерес к технике и конкретному результату.",
        "I": "Аналитическое мышление, любознательность, склонность разбираться в сложных системах.",
        "A": "Креативность, образность мышления, стремление создавать новое и выражать себя.",
        "S": "Эмпатия, коммуникация, готовность поддерживать, обучать и сопровождать людей.",
        "E": "Инициативность, лидерские качества, способность убеждать и организовывать процессы.",
        "C": "Системность, аккуратность, внимательность к деталям, любовь к порядку и структуре.",
    }


def environment_map():
    return {
        "R": "Практико-ориентированная среда, техника, оборудование, понятный и видимый результат.",
        "I": "Среда, где нужно исследовать, анализировать, искать закономерности и решать сложные задачи.",
        "A": "Гибкая среда, где ценятся идеи, оригинальность, эстетика и свобода подхода.",
        "S": "Работа с людьми, обучением, поддержкой, сопровождением и взаимодействием.",
        "E": "Среда, где есть цели, переговоры, организация, влияние и движение к результату.",
        "C": "Структурированная система, данные, документы, правила, регламенты и порядок.",
    }


def risks_map():
    return {
        "R": "Слишком абстрактная теория без практического выхода.",
        "I": "Поверхностная суета и постоянная спешка без времени на анализ.",
        "A": "Жёсткая регламентация, шаблонность и отсутствие пространства для идей.",
        "S": "Изоляция, эмоционально холодная среда, мало контакта с людьми.",
        "E": "Пассивная и рутинная деятельность без влияния на решения.",
        "C": "Хаос, неопределённость и отсутствие понятной системы.",
    }


# ----------------------------
# График
# ----------------------------
def make_bar_chart(scores: dict):
    letters = ["R", "I", "A", "S", "E", "C"]
    values = [scores.get(x, 0) for x in letters]

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    bars = ax.bar(letters, values, width=0.62)

    for bar, letter, value in zip(bars, letters, values):
        bar.set_color(TYPE_COLORS[letter])
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.18,
            str(value),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

    ax.set_title("Профиль профессиональных интересов RIASEC", fontsize=14, pad=12)
    ax.set_ylabel("Баллы", fontsize=11)
    ax.set_ylim(0, max(14, max(values) + 2))
    ax.grid(axis="y", linestyle="--", alpha=0.20)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_alpha(0.3)
    ax.spines["bottom"].set_alpha(0.3)
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=10)

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ----------------------------
# Стили
# ----------------------------
def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="HeroKicker",
        fontName="DejaVu-Bold",
        fontSize=11,
        leading=14,
        textColor=ACCENT,
        alignment=TA_CENTER,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontName="DejaVu-Bold",
        fontSize=25,
        leading=31,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        fontName="DejaVu",
        fontSize=11,
        leading=16,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="HeroCode",
        fontName="DejaVu-Bold",
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontName="DejaVu-Bold",
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="CardTitle",
        fontName="DejaVu-Bold",
        fontSize=12,
        leading=15,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontName="DejaVu",
        fontSize=10.5,
        leading=15,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="BodySmall",
        fontName="DejaVu",
        fontSize=9.1,
        leading=12.5,
        textColor=MUTED,
        alignment=TA_LEFT,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="Label",
        fontName="DejaVu-Bold",
        fontSize=9,
        leading=11,
        textColor=PRIMARY_SOFT,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="Value",
        fontName="DejaVu",
        fontSize=10,
        leading=13,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="MiniTypeCode",
        fontName="DejaVu-Bold",
        fontSize=16,
        leading=18,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="CompactBody",
        fontName="DejaVu",
        fontSize=8.9,
        leading=10.8,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="TopCardLetter",
        fontName="DejaVu-Bold",
        fontSize=20,
        leading=22,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="TopCardTitle",
        fontName="DejaVu-Bold",
        fontSize=9.6,
        leading=11,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="TopCardText",
        fontName="DejaVu",
        fontSize=8.6,
        leading=10.5,
        textColor=MUTED,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        name="CompactTypeTitle",
        fontName="DejaVu-Bold",
        fontSize=10.8,
        leading=12.5,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="FinalBrandTitle",
        fontName="DejaVu-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="FinalBrandBody",
        fontName="DejaVu",
        fontSize=9.3,
        leading=13,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=3,
    ))

    return styles


# ----------------------------
# Header / Footer
# ----------------------------
def add_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.7)
    canvas.line(1.8 * cm, height - 1.25 * cm, width - 1.8 * cm, height - 1.25 * cm)
    canvas.line(1.8 * cm, 1.15 * cm, width - 1.8 * cm, 1.15 * cm)

    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.8 * cm, 0.72 * cm, "Профориентационный отчёт")
    canvas.drawRightString(width - 1.8 * cm, 0.72 * cm, f"Стр. {doc.page}")
    canvas.restoreState()


# ----------------------------
# UI-блоки PDF
# ----------------------------
def make_person_card(name, age, contact, city, category, styles):
    rows = [
        [
            Paragraph("<b>Имя</b><br/>" + (name.strip() if name else "Не указано"), styles["Value"]),
            Paragraph("<b>Возраст</b><br/>" + (str(age).strip() if age else "Не указан"), styles["Value"]),
        ],
        [
            Paragraph("<b>Категория</b><br/>" + (category.strip() if category else "Не указана"), styles["Value"]),
            Paragraph("<b>Дата</b><br/>" + datetime.now().strftime("%d.%m.%Y"), styles["Value"]),
        ],
        [
            Paragraph("<b>Контакт</b><br/>" + (contact.strip() if contact else "Не указан"), styles["Value"]),
            Paragraph("<b>Город</b><br/>" + (city.strip() if city else "Не указан"), styles["Value"]),
        ],
    ]

    table = Table(rows, colWidths=[7.7 * cm, 7.7 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


def make_top_types_row(top3, styles):
    cards = []

    for letter in top3:
        info = types_data[letter]

        inner = [
            Paragraph(letter, styles["TopCardLetter"]),
            Paragraph(TYPE_CARD_TITLES[letter].replace("\n", "<br/>"), styles["TopCardTitle"]),
            Paragraph(TYPE_SHORT[letter], styles["TopCardText"]),
        ]

        frame = KeepInFrame(4.9 * cm, 2.7 * cm, inner, mode="shrink")

        card = Table([[frame]], colWidths=[5.15 * cm], rowHeights=[2.85 * cm])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBEFORE", (0, 0), (0, 0), 3, TYPE_COLORS_RL[letter]),
        ]))
        cards.append(card)

    wrap = Table([cards], colWidths=[5.15 * cm, 5.15 * cm, 5.15 * cm])
    wrap.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return wrap


def make_score_table(scores: dict):
    ordered = sorted_score_list(scores)
    data = [["Код", "Тип", "Баллы", "Комментарий"]]

    max_score = max(scores.values()) if scores else 0

    for letter, value in ordered:
        if value >= max_score - 1:
            comment = "Ведущее направление"
        elif value >= 8:
            comment = "Устойчивый интерес"
        elif value >= 5:
            comment = "Средняя выраженность"
        else:
            comment = "Менее выражено"

        data.append([letter, TYPE_LABELS[letter], str(value), comment])

    table = Table(data, colWidths=[1.5 * cm, 5.2 * cm, 2.1 * cm, 7.0 * cm])
    style = TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ])

    for i, (letter, _) in enumerate(ordered, start=1):
        style.add("TEXTCOLOR", (0, i), (0, i), TYPE_COLORS_RL[letter])
        style.add("FONTNAME", (0, i), (0, i), "DejaVu-Bold")

    table.setStyle(style)
    return table


def make_type_card(letter: str, styles):
    info = types_data[letter]
    strengths = strengths_map()[letter]
    environment = environment_map()[letter]
    risks = risks_map()[letter]
    fields = ", ".join(info["fields"][:5])

    content = [[
        Paragraph(
            f"<font color='{TYPE_COLORS[letter]}'><b>{letter}</b></font>  {info['name']}",
            styles["CompactTypeTitle"]
        )
    ], [
        Paragraph(info["text"], styles["CompactBody"])
    ], [
        Paragraph(f"<b>Сильные стороны:</b> {strengths}", styles["CompactBody"])
    ], [
        Paragraph(f"<b>Подходящая среда:</b> {environment}", styles["CompactBody"])
    ], [
        Paragraph(f"<b>Что может утомлять:</b> {risks}", styles["CompactBody"])
    ], [
        Paragraph(f"<b>Подходящие направления:</b> {fields}", styles["CompactBody"])
    ]]

    table = Table(content, colWidths=[16.2 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LINEBEFORE", (0, 0), (0, 0), 3, TYPE_COLORS_RL[letter]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def make_interest_table(items):
    data = [["Сфера интересов", "Балл", "Уровень"]]
    for item in items:
        data.append([item["name"], str(item["score"]), item["level"]])

    table = Table(data, colWidths=[9.0 * cm, 2.2 * cm, 4.8 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.8, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


# ----------------------------
# Основная функция
# ----------------------------
def create_pdf(name, age, contact, city, category, scores, code, interest_results):
    if interest_results is None:
        interest_results = []

    display_name = get_display_name(name)
    safe_name = sanitize_filename(display_name)
    filename = f"result_{safe_name}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=1.7 * cm,
    )

    styles = create_styles()
    story = []

    top3 = get_top_types(scores, 3)
    recommended_fields = build_recommended_fields(top3)
    high_interests, mid_interests, low_interests = build_interest_groups(interest_results)

    # ----------------------------
    # 1. Обложка
    # ----------------------------
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("Индивидуальный профориентационный отчёт", styles["HeroKicker"]))
    story.append(Paragraph("ПРОФИЛЬ ИНТЕРЕСОВ И ПРОФЕССИОНАЛЬНЫХ СКЛОННОСТЕЙ", styles["ReportTitle"]))
    story.append(Paragraph(
        "Отчёт составлен по итогам прохождения тестирования по модели RIASEC",
        styles["ReportSubtitle"]
    ))
    story.append(Spacer(1, 0.55 * cm))

    story.append(Paragraph(f"Ваш код: <b>{code}</b>", styles["HeroCode"]))
    story.append(Paragraph(get_code_text(code), styles["ReportSubtitle"]))
    story.append(Spacer(1, 0.45 * cm))

    story.append(make_top_types_row(top3, styles))
    story.append(Spacer(1, 0.55 * cm))

    story.append(make_person_card(display_name, age, contact, city, category, styles))
    story.append(Spacer(1, 0.55 * cm))

    if category == "Подросток":
        hero_summary = (
            f"Профиль <b>{code}</b> показывает, какие форматы деятельности и учебные направления "
            f"могут быть наиболее естественными и интересными именно сейчас. "
            f"Главные опоры этого результата — типы "
            f"<b>{TYPE_LABELS[top3[0]]}</b>, <b>{TYPE_LABELS[top3[1]]}</b> и <b>{TYPE_LABELS[top3[2]]}</b>."
        )
    else:
        hero_summary = (
            f"Профиль <b>{code}</b> показывает, в каких рабочих форматах и профессиональных ролях "
            f"человек чаще всего раскрывается естественно и устойчиво. "
            f"Главные опоры этого результата — типы "
            f"<b>{TYPE_LABELS[top3[0]]}</b>, <b>{TYPE_LABELS[top3[1]]}</b> и <b>{TYPE_LABELS[top3[2]]}</b>."
        )

    story.append(Paragraph(hero_summary, styles["Body"]))
    story.append(Spacer(1, 2.2 * cm))
    story.append(Paragraph(
        "Отчёт помогает сузить круг направлений и лучше понять свои сильные профессиональные склонности.",
        styles["ReportSubtitle"]
    ))
    story.append(PageBreak())

    # ----------------------------
    # 2. Профиль RIASEC
    # ----------------------------
    story.append(Paragraph("1. Общий профиль RIASEC", styles["SectionTitle"]))
    story.append(Paragraph(
        "Шесть шкал RIASEC показывают, какие виды деятельности вызывают у человека "
        "наибольший интерес и где выше вероятность естественной вовлечённости.",
        styles["Body"]
    ))
    story.append(make_score_table(scores))
    story.append(Spacer(1, 0.35 * cm))
    story.append(Image(make_bar_chart(scores), width=16.2 * cm, height=9.0 * cm))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "Чем выше балл по шкале, тем сильнее интерес к соответствующему типу задач, среды и профессиональной роли.",
        styles["BodySmall"]
    ))
    story.append(PageBreak())

    # ----------------------------
    # 3. Три ведущих типа
    # ----------------------------
    story.append(Paragraph("2. Три ведущих типа личности", styles["SectionTitle"]))
    story.append(Paragraph(
        "Три направления, которые сильнее всего проявились в профиле.",
        styles["BodySmall"]
    ))

    for idx, letter in enumerate(top3):
        story.append(make_type_card(letter, styles))
        if idx != len(top3) - 1:
            story.append(Spacer(1, 0.10 * cm))

    story.append(PageBreak())

    # ----------------------------
    # 4. Карта интересов
    # ----------------------------
    if interest_results:
        story.append(Paragraph(
            "3. Карта интересов подростка" if category == "Подросток" else "3. Карта интересов взрослого",
            styles["SectionTitle"]
        ))

        if category == "Подросток":
            intro_text = (
                "Этот блок помогает увидеть сферы, которые вызывают наибольший отклик. "
                "Именно их полезно учитывать при выборе профиля обучения, кружков, дополнительных занятий "
                "и первых профессиональных проб."
            )
        else:
            intro_text = (
                "Этот блок помогает увидеть сферы, которые вызывают наибольший отклик. "
                "Именно они могут стать опорой для профессионального развития, повышения квалификации "
                "или смены карьерного направления."
            )

        story.append(Paragraph(intro_text, styles["Body"]))

        top_interests = interest_results[:10]
        story.append(make_interest_table(top_interests))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(build_interest_summary(category, interest_results), styles["Body"]))

        if high_interests:
            story.append(Paragraph(
                "<b>Высокий интерес:</b> " + ", ".join(x["name"] for x in high_interests[:6]),
                styles["BodySmall"]
            ))
        if mid_interests:
            story.append(Paragraph(
                "<b>Средний интерес:</b> " + ", ".join(x["name"] for x in mid_interests[:6]),
                styles["BodySmall"]
            ))

        story.append(PageBreak())

    # ----------------------------
    # 5. Рекомендации
    # ----------------------------
    story.append(CondPageBreak(6 * cm))
    story.append(Paragraph("4. Практические рекомендации", styles["SectionTitle"]))

    story.append(Paragraph(
        f"С учётом результатов теста стоит обратить внимание на такие направления: "
        f"<b>{', '.join(recommended_fields)}</b>.",
        styles["Body"]
    ))

    if category == "Подросток":
        rec_1 = (
            "Не стоит выбирать профессию слишком жёстко и окончательно уже сейчас. "
            "Гораздо полезнее смотреть на то, какие предметы, занятия и форматы деятельности "
            "дают больше интереса, энергии и чувства вовлечённости."
        )
        rec_2 = (
            "Лучше проверять выводы не только размышлением, но и практикой: кружки, проекты, "
            "олимпиады, профильные курсы, общение со специалистами, пробные задания."
        )
        rec_3 = (
            "Если выбор даётся трудно, результат отчёта полезно сопоставить с успеваемостью, "
            "мотивацией, особенностями характера и консультацией со специалистом."
        )
        final_text = (
            f"Профиль <b>{code}</b> говорит о том, что наиболее перспективными будут те направления, "
            f"где можно сочетать качества типов <b>{TYPE_LABELS[top3[0]]}</b>, "
            f"<b>{TYPE_LABELS[top3[1]]}</b> и <b>{TYPE_LABELS[top3[2]]}</b>. "
            "Именно это сочетание полезно учитывать при выборе учебного профиля и первых шагов в самоопределении."
        )
    else:
        rec_1 = (
            "При выборе следующего карьерного шага важно учитывать не только интерес, "
            "но и уже накопленный опыт, сильные навыки, образ жизни и реальные возможности перехода."
        )
        rec_2 = (
            "Полезно проверить выводы через практику: короткие программы обучения, пробные задачи, "
            "стажировки, консультации, анализ смежных ролей и специализаций."
        )
        rec_3 = (
            "Если вопрос смены профессии остаётся открытым, этот отчёт лучше рассматривать "
            "как основу для уточнения вектора, а не как единственное решение."
        )
        final_text = (
            f"Профиль <b>{code}</b> показывает, что наиболее естественная профессиональная реализация "
            f"часто находится там, где можно использовать качества типов "
            f"<b>{TYPE_LABELS[top3[0]]}</b>, <b>{TYPE_LABELS[top3[1]]}</b> и <b>{TYPE_LABELS[top3[2]]}</b>. "
            "Это сочетание полезно учитывать при уточнении роли, специализации или смене направления."
        )

    story.append(Paragraph(rec_1, styles["Body"]))
    story.append(Paragraph(rec_2, styles["Body"]))
    story.append(Paragraph(rec_3, styles["Body"]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Итоговое заключение", styles["SectionTitle"]))
    story.append(Paragraph(final_text, styles["Body"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Этот отчёт не определяет профессию окончательно. Он помогает понять, "
        "какие направления и форматы деятельности стоит рассматривать в первую очередь.",
        styles["BodySmall"]
    ))

    story.append(Spacer(1, 1.8 * cm))

    final_brand = Table([[
        Paragraph(
            "<b>Вероника Илясова</b><br/>"
            "Профориентация, консультации и помощь в выборе профессионального направления<br/><br/>"
            "ИП Илясова Вероника Ивановна<br/>"
            "ОГРНИП 326784700049688<br/>"
            "ИНН 352402248527<br/><br/>"
            "© 2026 Вероника Илясова. Все права защищены.",
            styles["FinalBrandBody"]
        )
    ]], colWidths=[16.2 * cm])

    final_brand.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(final_brand)

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return filename