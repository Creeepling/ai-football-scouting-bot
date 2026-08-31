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
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#475569'),
        spaceAfter=4
    )

    section_header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=4,
        spaceAfter=1.5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155'),
        spaceAfter=1.5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=9,
        firstLineIndent=-5,
        spaceAfter=1
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("AI Football Scouting Assistant -- Project Case Study", title_style))
    story.append(Paragraph("Серверлесс AI-платформа аналитики: детерминированный стат-движок в Python + ReAct LLM-оркестрация", subtitle_style))

    # Meta Table
    meta_html = "<b>GitHub Repository:</b> <font color='#2563EB'><u><a href='https://github.com/Creeepling/ai-football-scouting-bot'>https://github.com/Creeepling/ai-football-scouting-bot</a></u></font><br/>" \
                "<b>Стек технологий:</b> Python 3.11, Google Cloud Functions (Gen 2), LangChain, Wyscout API, MongoDB Atlas, Cloud Storage, Matplotlib, Telegram API"
    meta_p = Paragraph(meta_html, callout_style)
    meta_table = Table([[meta_p]], colWidths=[180 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 2.5))

    # 1. Архитектурная идея и проблема
    story.append(Paragraph("1. Архитектурная философия и решаемая проблема", section_header_style))
    story.append(Paragraph(
        "<b>Архитектурный принцип:</b> Полное разделение математических вычислений и языковой генерации. Статистика, Per-90, перцентили и Байесовские сглаживания рассчитываются <b>детерминированно в Python/Pandas</b>. LLM <b>не является источником числовой истины</b> и используется исключительно для распознавания сущностей (Entity Resolution), оркестрации инструментов (ReAct Tool Calling) и контекстной тактической интерпретации.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Проблема:</b> Скаутинг требует ручного сопоставления профилей Transfermarkt и Wyscout, вычисления перцентилей относительно лиги/позиции, построения графиков и написания резюме. Продукт автоматизирует этот цикл от ссылки до готового досье со скаутинг-картой и экспертным резюме в Telegram.",
        body_style
    ))

    # 2. Пользователь
    story.append(Paragraph("2. Кто пользователь", section_header_style))
    story.append(Paragraph("- Спортивные директоры и селекционные отделы футбольных клубов.", bullet_style))
    story.append(Paragraph("- Футбольные скауты и матчевые аналитики, проводящие первичный скрининг игроков.", bullet_style))
    story.append(Paragraph("- Футбольные агентства для подготовки аналитических досье и презентаций кандидатов.", bullet_style))

    # 3. Личный вклад
    story.append(Paragraph("3. Что именно сделано лично (Engineering Ownership)", section_header_style))
    story.append(Paragraph("- <b>Архитектура и Backend:</b> Спроектировал и реализовал модульный серверлесс-сервис на Python с изоляцией сессий через <b>contextvars</b> для потокобезопасной обработки запросов.", bullet_style))
    story.append(Paragraph("- <b>Детерминированный стат-движок:</b> Разработал формулы нормализации показателей: Per-90, перцентильные ранги по лигам и Байесовское сглаживание (<b>bayes_rank</b>) для метрик с малым числом попыток.", bullet_style))
    story.append(Paragraph("- <b>Data Pipelines & Агрегации:</b> Написал коннекторы к Wyscout API v3 и MongoDB Atlas со сложными агрегационными пайплайнами сезонной и матчевой статистики.", bullet_style))
    story.append(Paragraph("- <b>AI Agent & Tool Calling:</b> Построил ReAct-агента на базе LangChain с набором инструментов (поиск сущностей, выбор сезона, глубокий анализ метрик и расчет игровых позиций).", bullet_style))
    story.append(Paragraph("- <b>Генератор графических отчетов:</b> Реализовал рендеринг скаутинг-карт, гистограмм распределения, тепловых карт и круговых диаграмм на Matplotlib/Seaborn с контролем утечек памяти.", bullet_style))
    story.append(Paragraph("- <b>DevOps & Безопасность:</b> Настроил zero-secret архитектуру через GCP Secret Manager и автоматизировал CI/CD деплой в GitHub Actions через Workload Identity Federation (WIF).", bullet_style))

    # 4. Архитектура системы
    story.append(Paragraph("4. Архитектура системы", section_header_style))
    story.append(Paragraph(
        "<b>Поток данных:</b> Telegram Webhook <b>-></b> GCP Cloud Function (Router) <b>-></b> Thread-Safe Context (contextvars) <b>-></b> ReAct Agent (LangChain) <b>-></b> Data Layer (Wyscout API, MongoDB Atlas, Serper API) <b>-></b> Deterministic Engine (Pandas / NumPy) <b>-></b> Visualization Engine (Matplotlib / Seaborn) <b>-></b> GCS Session Store <b>-></b> Telegram Bot API.",
        body_style
    ))

    # 5. Стек и источники данных
    story.append(Paragraph("5. Используемый стек, API и источники данных", section_header_style))
    story.append(Paragraph("- <b>Core & Serverless:</b> Python 3.11, Google Cloud Functions (Gen 2 / Cloud Run), Flask / Functions Framework, PyMongo, Pydantic.", bullet_style))
    story.append(Paragraph("- <b>AI / LLM & Оркестрация:</b> LangChain, Google Gemini API / OpenAI (<b>gemini-3-flash-preview</b>), Google Serper API.", bullet_style))
    story.append(Paragraph("- <b>Базы данных и хранилище:</b> MongoDB Atlas (событийная статистика матчей), Google Cloud Storage (JSON-сессии и справочники метрик).", bullet_style))
    story.append(Paragraph("- <b>Data Science & Визуализация:</b> Pandas, NumPy, Matplotlib, Seaborn, Pillow.", bullet_style))
    story.append(Paragraph("- <b>Внешние сервисы:</b> Wyscout API v3 (профили, карьеры, сезоны, соревнования), Telegram Bot API.", bullet_style))

    # 6. Применение AI / LLM и Tool Calling
    story.append(Paragraph("6. Где и как используется AI / LLM (Tool Calling)", section_header_style))
    story.append(Paragraph("- <b>Fuzzy Entity Resolution:</b> Парсинг неструктурированных ссылок Transfermarkt через Serper + LLM-экстрактор и точный маппинг на базу Wyscout.", bullet_style))
    story.append(Paragraph("- <b>ReAct Tool Orchestration:</b> Автономный выбор и вызов аналитических инструментов агентом в зависимости от контекста диалога (выбор сезона, срез метрики, тепловая карта, распределение позиций).", bullet_style))
    story.append(Paragraph("- <b>Tactical Scouting Synthesis:</b> Генерация экспертного резюме на базе перцентилей игрока (оценка баланса качеств, выявление аномалий и сильных сторон на фоне конкурентов по лиге).", bullet_style))

    # 7. Развертывание
    story.append(Paragraph("7. Развертывание и инфраструктура (DevOps)", section_header_style))
    story.append(Paragraph(
        "Сервис развернут в бессерверной среде <b>Google Cloud Functions (Gen 2)</b> с масштабированием в 0. Конфиденциальные ключи изолированы в <b>GCP Secret Manager</b> и динамически монтируются при запуске. Деплой автоматизирован через <b>GitHub Actions</b> с беспарольной аутентификацией через <b>Workload Identity Federation</b>.",
        body_style
    ))

    # 8. Что было сложным технически
    story.append(Paragraph("8. Что было сложным технически (Key Technical Challenges)", section_header_style))
    story.append(Paragraph("- <b>Small-Sample Variance:</b> Игрок с 2 успешными обводками из 2 получал 100-й перцентиль. Решено внедрением Байесовского сглаживания с учетом априорного веса 80-го перцентиля лиги.", bullet_style))
    story.append(Paragraph("- <b>Fuzzy Entity Matching:</b> Сопоставление локализованных имен и транслитераций Transfermarkt с жестким поисковым индексом Wyscout.", bullet_style))
    story.append(Paragraph("- <b>Matplotlib в Serverless:</b> Устранение утечек памяти в переиспользуемых контейнерах Cloud Functions через строгий вызов plt.close(fig) и бинарные потоки io.BytesIO.", bullet_style))
    story.append(Paragraph("- <b>Потокобезопасность:</b> Изоляция контекста запросов (chat_id, язык) без глобальных переменных через contextvars.", bullet_style))

    # 9. Что бы сегодня сделал иначе
    story.append(Paragraph("9. Что бы сегодня сделал иначе (Future Evolution)", section_header_style))
    story.append(Paragraph("- <b>Асинхронные очереди (Cloud Tasks / Pub/Sub):</b> Вынесение генерации тяжелых графиков в фоновые воркеры с пуш-уведомлением для исключения рисков вебхук-таймаута Telegram.", bullet_style))
    story.append(Paragraph("- <b>Similarity Search (Поиск аналогов):</b> Добавление векторного поиска (Vector DB / pgvector) по вектору перцентилей для автоматического подбора похожих игроков (Player Comparison).", bullet_style))
    story.append(Paragraph("- <b>Кэширование (Redis):</b> Кэширование профилей и агрегированных срезов Wyscout для минимизации расходов на вызовы сторонних API.", bullet_style))
    story.append(Paragraph("- <b>Modern LCEL & Structured Output:</b> Переход на Pydantic Function Calling в LangChain вместо парсинга строк ReAct.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Brief PDF generated successfully at: {output_path}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "AI_Football_Scouting_Bot_Brief.pdf"
    create_brief_pdf(out_file)
