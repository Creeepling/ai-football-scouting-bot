import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Cyrillic-capable fonts
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont('Arial', 8)
        self.setFillColor(colors.HexColor('#64748B'))

        # Header (page > 1)
        if self._pageNumber > 1:
            self.drawString(15 * mm, 287 * mm, "AI Football Scouting Assistant -- Executive Technical Case Study")
            self.setStrokeColor(colors.HexColor('#CBD5E1'))
            self.setLineWidth(0.5)
            self.line(15 * mm, 284 * mm, 195 * mm, 284 * mm)

        # Footer
        page_text = f"Страница {self._pageNumber} из {page_count}"
        self.drawRightString(195 * mm, 10 * mm, page_text)
        self.drawString(15 * mm, 10 * mm, "GitHub: https://github.com/Creeepling/ai-football-scouting-bot | Confidential")
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.5)
        self.line(15 * mm, 14 * mm, 195 * mm, 14 * mm)
        self.restoreState()


def create_brief_pdf(output_path="AI_Football_Scouting_Bot_Brief.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#475569'),
        spaceAfter=5
    )

    section_header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=2
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=1.5
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("AI Football Scouting Assistant -- Project Case Study", title_style))
    story.append(Paragraph("Серверлесс AI-платформа для автоматизированного скаутинга, расчета перцентилей и генерации аналитических отчетов", subtitle_style))

    # Meta Table
    meta_html = "<b>GitHub Repository:</b> <font color='#2563EB'><u><a href='https://github.com/Creeepling/ai-football-scouting-bot'>https://github.com/Creeepling/ai-football-scouting-bot</a></u></font><br/>" \
                "<b>Стек технологий:</b> Python 3.11, Google Cloud Functions (Gen 2), LangChain, Wyscout API, MongoDB Atlas, Cloud Storage, Matplotlib, Telegram API"
    meta_p = Paragraph(meta_html, callout_style)
    meta_table = Table([[meta_p]], colWidths=[180 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 3))

    # 1. Проблема
    story.append(Paragraph("1. Какую конкретную проблему решает продукт", section_header_style))
    story.append(Paragraph(
        "Первичный скаутинг и оценка кандидатов требует ручного сбора статистики из разрозненных источников (Transfermarkt, Wyscout), вычисления позиции-специфичных перцентилей относительно лиги, отрисовки графиков и написания текстовых заключений. Продукт полностью автоматизирует этот аналитический цикл: по входящей ссылке на игрока система извлекает метаданные, рассчитывает перцентили на основе базы матчей лиги, строит визуальные скаутинг-карты и формирует экспертное тактическое резюме в Telegram.",
        body_style
    ))

    # 2. Пользователь
    story.append(Paragraph("2. Кто пользователь", section_header_style))
    story.append(Paragraph("- Спортивные директоры и селекционные отделы профессиональных футбольных клубов.", bullet_style))
    story.append(Paragraph("- Футбольные скауты и матчевые аналитики, проводящие первичный скрининг игроков.", bullet_style))
    story.append(Paragraph("- Футбольные агентства для оперативной подготовки аналитических досье и презентаций кандидатов.", bullet_style))

    # 3. Личный вклад
    story.append(Paragraph("3. Что именно я сделал лично (Architecture & Core Engineering)", section_header_style))
    story.append(Paragraph("- <b>Архитектура и Backend:</b> Спроектировал и реализовал модульный серверлесс-сервис на Python с изоляцией сессий через <b>contextvars</b> для потокобезопасной обработки запросов.", bullet_style))
    story.append(Paragraph("- <b>Статистический движок:</b> Разработал алгоритмы нормализации показателей: расчет Per-90, перцентильных рангов и Байесовского сглаживания (Bayes Rank) для метрик с малым числом попыток.", bullet_style))
    story.append(Paragraph("- <b>Data Pipelines & Агрегации:</b> Написал коннекторы к Wyscout API v3 и MongoDB Atlas со сложными агрегационными пайплайнами сезонной и матчевой статистики.", bullet_style))
    story.append(Paragraph("- <b>AI Agent & Инструменты:</b> Построил ReAct-агента на базе LangChain с набором инструментов (поиск сущностей, выбор сезона, глубокий анализ метрик и расчет игровых позиций).", bullet_style))
    story.append(Paragraph("- <b>Генератор графических отчетов:</b> Реализовал рендеринг скаутинг-карт, гистограмм распределения по лиге, тепловых карт и круговых диаграмм на Matplotlib/Seaborn с контролем утечек памяти.", bullet_style))
    story.append(Paragraph("- <b>DevOps & Безопасность:</b> Настроил zero-secret архитектуру через GCP Secret Manager и автоматизировал CI/CD деплой в GitHub Actions через Workload Identity Federation (WIF).", bullet_style))

    # 4. Архитектура системы
    story.append(Paragraph("4. Архитектура системы", section_header_style))
    story.append(Paragraph(
        "<b>Поток данных:</b> Telegram Webhook <b>-></b> GCP Cloud Function (Router) <b>-></b> Thread-Safe Context <b>-></b> ReAct Agent (LangChain) <b>-></b> External APIs (Wyscout API, MongoDB Atlas, Serper API) <b>-></b> Statistical Engine (Pandas / NumPy) <b>-></b> Visualization Engine (Matplotlib / Seaborn) <b>-></b> GCS Session Store <b>-></b> Telegram Bot API.",
        body_style
    ))

    # 5. Стек и источники данных
    story.append(Paragraph("5. Используемый стек, API и источники данных", section_header_style))
    story.append(Paragraph("- <b>Core & Serverless:</b> Python 3.11, Google Cloud Functions (Gen 2 / Cloud Run), Flask / Functions Framework, PyMongo, Pydantic.", bullet_style))
    story.append(Paragraph("- <b>AI / LLM & Оркестрация:</b> LangChain, Google Gemini API / OpenAI (<b>gemini-3-flash-preview</b>), Google Serper API.", bullet_style))
    story.append(Paragraph("- <b>Базы данных и хранилище:</b> MongoDB Atlas (событийная статистика матчей), Google Cloud Storage (JSON-сессии и справочники метрик).", bullet_style))
    story.append(Paragraph("- <b>Data Science & Визуализация:</b> Pandas, NumPy, Matplotlib, Seaborn, Pillow.", bullet_style))
    story.append(Paragraph("- <b>Внешние сервисы:</b> Wyscout API v3 (профили, карьеры, сезоны, соревнования), Telegram Bot API.", bullet_style))

    # 6. Применение AI / LLM
    story.append(Paragraph("6. Где и как используется AI / LLM", section_header_style))
    story.append(Paragraph("- <b>Entity Extraction & Resolution:</b> Извлечение метаданных игрока из Transfermarkt и точное сопоставление с профилем в базе Wyscout.", bullet_style))
    story.append(Paragraph("- <b>ReAct Function Calling:</b> Автономный выбор и вызов аналитических инструментов агентом в зависимости от контекста диалога.", bullet_style))
    story.append(Paragraph("- <b>Tactical Scouting Synthesis:</b> Генерация экспертного резюме на базе перцентилей игрока (оценка баланса качеств, выявление аномалий и сильных сторон на фоне конкурентов по лиге).", bullet_style))

    # 7. Развертывание
    story.append(Paragraph("7. Как система была развернута (DevOps / Infrastructure)", section_header_style))
    story.append(Paragraph(
        "Сервис развернут в бессерверной среде <b>Google Cloud Functions (Gen 2)</b> с автоматическим масштабированием от 0. Конфиденциальные ключи изолированы в <b>GCP Secret Manager</b> и динамически монтируются при запуске. Деплой автоматизирован через <b>GitHub Actions</b> с беспарольной аутентификацией через <b>Workload Identity Federation</b>.",
        body_style
    ))

    # 8. Фактический результат
    story.append(Paragraph("8. Какой фактический результат получился и статус использования", section_header_style))
    story.append(Paragraph(
        "Создан готовый к эксплуатации AI-ассистент с поддержкой двух языков (EN/RU). Обеспечена сквозная автоматизация: от входящей ссылки до готового аналитического среза со скаутинг-картой и текстовым отчетом без участия аналитика. Продукт применялся селекционной командой для экспресс-оценки кандидатов и формирования лонг-листов трансферных целей.",
        body_style
    ))

    # 9. Ограничения и улучшение
    story.append(Paragraph("9. Какие есть ограничения системы и что улучшил бы сейчас", section_header_style))
    story.append(Paragraph("- <b>Асинхронные очереди (Cloud Tasks / Pub/Sub):</b> Вынесение генерации тяжелых графиков в фоновые воркеры с пуш-уведомлением для исключения рисков вебхук-таймаута.", bullet_style))
    story.append(Paragraph("- <b>Similarity Search (Поиск аналогов):</b> Добавление векторного поиска (Vector DB / pgvector) по вектору перцентилей для автоматического поиска похожих игроков (Player Comparison).", bullet_style))
    story.append(Paragraph("- <b>Кэширование запросов (Redis):</b> Кэширование профилей и агрегированных срезов Wyscout для минимизации расходов на вызовы сторонних API.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Brief PDF generated successfully at: {output_path}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "AI_Football_Scouting_Bot_Brief.pdf"
    create_brief_pdf(out_file)
