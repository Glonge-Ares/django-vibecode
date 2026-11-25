#!/usr/bin/env python3
"""Generate the lab-work report (GOST 7.32-2017 layout) as .docx.

Usage:
    uv run --with python-docx report/generate_report.py --pages N

Output: report/Отчёт_ЛР.docx
The --pages value is stated in the abstract (реферат); pass the page count
from the converted PDF to make it exact (two-pass generation).
"""

import argparse
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = Path(__file__).parent / "Отчёт_ЛР.docx"

TBL = 5          # tables in the main text
SRC = 10         # bibliography entries
APP = 3          # appendices


def new_doc():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(14)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), "Times New Roman")
    pf = style.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.first_line_indent = Cm(1.25)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for sec in doc.sections:
        setup_section(sec)
    return doc


def setup_section(sec):
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(3)
    sec.right_margin = Cm(1.5)
    sec.top_margin = Cm(2)
    sec.bottom_margin = Cm(2)


def para(doc, text="", *, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False,
         indent=1.25, size=14, font=None, keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = align
    p.paragraph_format.first_line_indent = Cm(indent) if indent is not None else None
    if keep:
        p.paragraph_format.keep_with_next = True
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.font.size = Pt(size)
        if font:
            r.font.name = font
            r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    return p


def h1(doc, text, page_break=False):
    if page_break:
        doc.add_page_break()
    p = para(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, indent=0, keep=True)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    return p


def h2(doc, text):
    p = para(doc, text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, indent=0, keep=True)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    return p


def item(doc, text, marker="—"):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(1.25)
    p.paragraph_format.first_line_indent = Cm(-0.6)
    r = p.add_run(f"{marker} {text}")
    r.font.size = Pt(14)
    return p


def code(doc, lines):
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.line_spacing = 1
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line)
        r.font.name = "Courier New"
        r.font.size = Pt(12)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")


def table(doc, headers, rows, caption):
    cap = para(doc, caption, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, indent=0, keep=True)
    cap.paragraph_format.space_before = Pt(8)
    cap.paragraph_format.space_after = Pt(2)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, htext in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
        cell.paragraphs[0].paragraph_format.line_spacing = 1
        run = cell.paragraphs[0].add_run(htext)
        run.bold = True
        run.font.size = Pt(14)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].paragraphs[0].paragraph_format.first_line_indent = Cm(0)
            cells[i].paragraphs[0].paragraph_format.line_spacing = 1
            run = cells[i].paragraphs[0].add_run(val)
            run.font.size = Pt(14)
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(6)
    after.paragraph_format.line_spacing = 1
    return t


def page_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)
    run.font.size = Pt(14)
    run.font.name = "Times New Roman"


def build(pages: int):
    doc = new_doc()

    # ---------------- title page (section 1, no footer) ----------------
    para(doc, "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=False)
    para(doc, "РОССИЙСКОЙ ФЕДЕРАЦИИ", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
    para(doc, "", indent=0)
    para(doc, "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
    para(doc, "ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
    para(doc, "«___________________________________»", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
    para(doc, "", indent=0)
    para(doc, "Кафедра «___________________________________»", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
    para(doc, "", indent=0)
    para(doc, "", indent=0)
    para(doc, "", indent=0)
    para(doc, "ОТЧЁТ", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=True)
    para(doc, "по лабораторной работе № ___", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=True)
    para(doc, "по дисциплине «___________________________________»", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=True)
    para(doc, "", indent=0)
    para(doc, "на тему:", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
    para(
        doc,
        "«Разработка веб-приложения для подготовки к экзаменам "
        "с использованием Django, PostgreSQL, Docker и протокола "
        "Model Context Protocol»",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        indent=0,
        bold=True,
    )
    para(doc, "", indent=0)
    para(doc, "", indent=0)
    para(doc, "Выполнил: студент гр. № ________", align=WD_ALIGN_PARAGRAPH.LEFT, indent=0)
    para(doc, "                      _____________________ (Ф.И.О.)", align=WD_ALIGN_PARAGRAPH.LEFT, indent=0)
    para(doc, "", indent=0)
    para(doc, "Проверил:                 _____________________ (Ф.И.О.)", align=WD_ALIGN_PARAGRAPH.LEFT, indent=0)
    for _ in range(3):
        para(doc, "", indent=0)
    para(doc, "_____________ (город) – 2026", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)

    # ---------------- main section (footer with page number) ----------------
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    setup_section(sec)
    sec.footer.is_linked_to_previous = False
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    page_field(fp)

    # РЕФЕРАТ
    para(doc, "РЕФЕРАТ", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, indent=0, keep=True)
    para(
        doc,
        f"Отчёт: {pages} с., таблиц: {tbl_count()}, источников: {SRC}, "
        f"приложений: {APP}.",
        indent=0,
    )
    para(
        doc,
        "В отчёте описана разработка демонстрационного веб-приложения "
        "«ExamPrep» для подготовки студентов к экзаменам. Реализованы: система "
        "экзаменов с вопросами трёх типов, автоматической проверкой, "
        "ограничением по времени и историей попыток; карточки для запоминания "
        "терминов (колоды, режим изучения с самооценкой и статистикой); "
        "администрирование контента через Django admin. Приложение построено "
        "на Django и PostgreSQL и целиком запускается средствами Docker "
        "Compose (ожидание готовности БД, миграции, health check). Разработан "
        "собственный MCP-сервер (Model Context Protocol) для доступа "
        "AI-агента к данным приложения, а также конфигурация агента: файл "
        "AGENTS.md, пользовательский Skill и файл opencode.json. Приведены "
        "архитектура, структура данных, состав и результаты тестирования "
        "(23 теста) и сценарий приёмочной проверки.",
    )
    para(
        doc,
        "Ключевые слова: подготовка к экзаменам, веб-приложение, Django, "
        "PostgreSQL, Docker, Docker Compose, карточки, тестирование, "
        "Model Context Protocol, MCP-сервер, AI-агент, AGENTS.md, Skill, "
        "opencode.",
        indent=0,
    )

    # СПИСОК СОКРАЩЕНИЙ
    para(doc, "", indent=0)
    para(doc, "СПИСОК СОКРАЩЕНИЙ И УСЛОВНЫХ ОБОЗНАЧЕНИЙ", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, indent=0, keep=True)
    for s in [
        "БД – база данных",
        "ИИ – искусственный интеллект",
        "СУБД – система управления базами данных",
        "ORM – объектно-реляционное отображение (object-relational mapping)",
        "SQL – язык структурированных запросов (structured query language)",
        "HTTP – протокол передачи гипертекста (hypertext transfer protocol)",
        "HTML – язык гипертекстовой разметки (hypertext markup language)",
        "CSS – каскадные таблицы стилей (cascading style sheets)",
        "CLI – интерфейс командной строки (command-line interface)",
        "WSGI – интерфейс сервера веб-приложений Python",
        "MCP – протокол контекста модели (Model Context Protocol)",
        "API – интерфейс программного приложения (application programming interface)",
        "REST – архитектурный стиль веб-сервисов",
    ]:
        item(doc, s)

    # 1 ЦЕЛЬ И ЗАДАЧИ
    h1(doc, "1 Цель и задачи работы", page_break=True)
    para(
        doc,
        "Цель работы – разработка и внедрение веб-приложения для подготовки "
        "к экзаменам, обеспечивающего самостоятельное прохождение тестов и "
        "запоминание терминов, с организацией выполнения в контейнерах "
        "Docker, подключением к приложению AI-агента через протокол MCP "
        "и оформлением сопроводительной документации для работы агента "
        "с кодовой базой.",
    )
    para(doc, "Для достижения поставленной цели решались следующие задачи:", indent=0)
    for i, t in enumerate(
        [
            "анализ предметной области «подготовка к экзаменам» и выбор "
            "технологического стека;",
            "проектирование модели данных экзаменов, попыток и карточек;",
            "реализация серверной части приложения на Django: представления, "
            "маршрутизация, шаблоны, административный интерфейс;",
            "реализация алгоритмов проверки ответов и подсчёта результатов, "
            "таймера экзамена и режима изучения карточек;",
            "написание модульных и интеграционных тестов (23 теста) "
            "и команд сидирования демонстрационных данных;",
            "контейнеризация приложения: Dockerfile, docker-compose.yml, "
            "скрипт ожидания и инициализации БД;",
            "разработка собственного MCP-сервера и конфигурации AI-агента "
            "(AGENTS.md, Skill, opencode.json);",
            "приёмочная проверка: запуск «с нуля» в Docker Compose, проверка "
            "веб-сценариев, тестов и инструментов MCP.",
        ]
    ):
        item(doc, t, marker=f"{i + 1})")
    para(
        doc,
        "Объект исследования – процесс подготовки обучающихся к экзаменам. "
        "Предмет исследования – веб-приложение для подготовки к экзаменам, "
        "развёрнутое в контейнерах и интегрированное со средствами "
        "машинного обучения через протокол MCP.",
    )
    para(
        doc,
        "Методы исследования: анализ предметной области и документации "
        "используемых технологий; объектно-ориентированное проектирование; "
        "компонентное тестирование; контейнеризация; протоколы HTTP и "
        "Model Context Protocol.",
    )

    # 2 ТЕОРЕТИЧЕСКАЯ ЧАСТЬ
    h1(doc, "2 Теоретическая часть и обоснование выбора технологий")
    h2(doc, "2.1 Среда выполнения: Django и язык Python")
    para(
        doc,
        "Django – высокоуровневый веб-фреймворк на Python, реализующий "
        "шаблон проектирования «model-template-view» и поставляющий "
        "собственные средства ORM, систему миграций, административный сайт, "
        "систему аутентификации и механизм шаблонов. Для учебного проекта "
        "выбор Django обусловлен: один фреймворк закрывает все слои "
        "приложения; миграции фиксируют изменения схемы БД в версионируемых "
        "файлах, что критично при совместной работе; встроенная админка "
        "позволяет без дополнительной разработки управлять контентом "
        "экзаменов и колод.",
    )
    h2(doc, "2.2 Система управления базами данных PostgreSQL")
    para(
        doc,
        "PostgreSQL – объектно-реляционная СУБД с развитой системой "
        "целостности (внешние ключи, проверочные ограничения), транзакциями "
        "уровня ACID и механизмом MVCC. В проекте PostgreSQL используется "
        "как основное хранилище: отношения «экзамен–вопрос–вариант», "
        "«попытка–ответ» поддерживаются внешними ключами, подсчёт "
        "результатов выполняется в транзакции. Взаимодействие "
        "с приложением осуществляется драйвером psycopg3 через ORM Django.",
    )
    h2(doc, "2.3 Технологии контейнеризации Docker и Docker Compose")
    para(
        doc,
        "Docker позволяет упаковать приложение вместе с окружением в "
        "образ, что исключает различия «работает у разработчика – не "
        "работает на стенде». Docker Compose описывает многосервисное "
        "развёртывание (приложение и СУБД) одним файлом: взаимосвязи, "
        "переменные окружения, тома данных, health checks. Для лабораторной "
        "работы это означает воспроизводимый запуск одной командой "
        "docker compose up --build на любой машине с установленным Docker.",
    )
    h2(doc, "2.4 Протокол MCP и настройка AI-агента")
    para(
        doc,
        "Model Context Protocol – открытый протокол, стандартизирующий "
        "обмен между ИИ-агентом и внешними инструментами: сервер предоставляет "
        "инструменты (tools) с описаниями и схемами аргументов, клиент "
        "вызывает их и получает структурированный результат. В работе "
        "разработан MCP-сервер на Python (транспорт stdio), который "
        "напрямую использует ORM Django и предоставляет агенту операции "
        "над данными приложения: получение списка экзаменов и вопросов, "
        "ключ ответов, статистику попыток, схему БД.",
    )
    para(
        doc,
        "Система агентов opencode настраивается файлами проекта: AGENTS.md – "
        "инструкция для агента с описанием проекта, команд и соглашений; "
        "Skill (папка .opencode/skills/<имя>/SKILL.md) – подробные пошаговые "
        "инструкции по типовым задачам развития проекта; opencode.json – "
        "конфигурация, подключающая MCP-сервер и указывающая AGENTS.md "
        "в качестве инструкций. Такое разделение позволяет агенту "
        "автономно ориентироваться в проекте, не запрашивая контекст "
        "заново в каждой сессии.",
    )

    # 3 ОПИСАНИЕ ВЫПОЛНЕННОЙ РАБОТЫ
    h1(doc, "3 Описание выполненной работы")
    h2(doc, "3.1 Архитектура и структура приложения")
    para(
        doc,
        "Приложение реализовано в виде двух бизнес-приложений Django в составе "
        "одного проекта: exams (экзамены) и flashcards (карточки). Представления "
        "серверные (шаблоны Django), оформление – единый каскадный файл "
        "style.css без сборочных инструментов. Статические файлы и шаблоны "
        "вынесены на уровень проекта. Структура репозитория приведена "
        "в приложении А.",
    )
    h2(doc, "3.2 Модель данных")
    para(
        doc,
        "Модель данных спроектирована с учётом двух сценариев запоминания: "
        "проверка знаний (экзамен с объективной проверкой ответов) и "
        "запоминание (карточки с самооценкой). Основные отношения "
        "представлены в таблицах 1 и 2.",
    )
    table(
        doc,
        ["Модель", "Назначение", "Основные поля"],
        [
            ["Exam", "экзамен (тест)", "title, slug, description, duration_minutes, is_published"],
            ["Question", "вопрос экзамена", "text, kind (single / multiple / text), points, order, expected_text"],
            ["Choice", "вариант ответа", "question, text, is_correct"],
            ["Attempt", "попытка прохождения", "user, exam, started_at, completed_at, score, max_score, expired"],
            ["Answer", "ответ в попытке", "attempt, question, selected_choices, text_answer, is_correct"],
        ],
        "Таблица 1 – Модели данных приложения exams",
    )
    table(
        doc,
        ["Модель", "Назначение", "Основные поля"],
        [
            ["Deck", "колода карточек", "title, slug, description, is_published"],
            ["Card", "карточка «термин – определение»", "deck, term, definition, position"],
            ["DeckResult", "итог сессии изучения", "deck, user, known_count, missed_count, created_at"],
        ],
        "Таблица 2 – Модели данных приложения flashcards",
    )
    para(
        doc,
        "Автоматическое поле slug генерируется из заголовка с разрешением "
        "коллизий суффиксами -2, -3. Оценка за вопрос вычисляется методом "
        "Question.is_correctly_answered: для одиночного и множественного "
        "выбора требуется точное совпадение множества правильных вариантов "
        "(частичные баллы не начисляются), для краткого ответа – "
        "сравнение без учёта регистра и пробелов с полем expected_text. "
        "Попытка создаётся один раз на пользователя и экзамен при первом "
        "открытии формы и переиспользуется при обновлении страницы, что "
        "исключает перезапуск таймера.",
    )
    h2(doc, "3.3 Пользовательские сценарии")
    for t in [
        "экзамены: список опубликованных экзаменов, страница описания, "
        "прохождение с обратным отсчётом (при duration_minutes > 0), отправка "
        "ответов, страница результата с разбором по вопросам, история попыток "
        "текущего пользователя;",
        "карточки: список колод, страница колоды с переворачиваемыми "
        "карточками и историей сессий, режим изучения «по одной карточке» "
        "со случайным порядком и кнопками «знал / не знал», итоговая "
        "оценка сессии сохраняется в DeckResult;",
        "аутентификация: просмотр списков доступен анонимно, прохождение "
        "экзаменов и изучение колод требует входа в систему; результаты "
        "доступны только их владельцу (проверяется тестом);",
        "администрирование: Django admin позволяет управлять экзаменами, "
        "вопросами и вариантами (inline-редактирование), колодами и "
        "карточками, просматривать попытки и результаты.",
    ]:
        item(doc, t)
    h2(doc, "3.4 Подготовка данных и тестирование")
    para(
        doc,
        "Команды seed_exams и seed_flashcards наполняют базу "
        "демонстрационным содержимым (3 экзамена на 13 вопросов, 2 колоды "
        "по 8 карточек) и идемпотентны: повторный запуск пропускает "
        "существующие записи. Тестовый набор (23 теста) покрывает правила "
        "проверки ответов всех трёх типов вопросов, генерацию slug, поток "
        "сдачи экзамена от входа до результата, права доступа к чужим "
        "результатам, поток изучения карточек (очередь в сессии, итоговая "
        " DeckResult), защиту от чужих и незавершённых сессий и "
        "идемпотентность сидирования.",
    )
    h2(doc, "3.5 Контейнеризация")
    para(
        doc,
        "Развёртывание описано в docker-compose.yml (таблица 3). Образ web "
        "собирается из python:3.13-slim, устанавливает зависимости из "
        "requirements.txt и использует entrypoint.sh: скрипт ожидает "
        "доступность PostgreSQL (до 30 попыток), выполняет миграции "
        "и передаёт управление команде контейнера. Каталог проекта "
        "монтируется в контейнер, что обеспечивает автоперезагрузку "
        "разработческого сервера Django при изменении кода.",
    )
    table(
        doc,
        ["Сервис", "Образ", "Назначение и настройки"],
        [
            ["db", "postgres:16-alpine", "СУБД; порт 5432 на хосте, том pgdata, health check pg_isready"],
            ["web", "сборка по Dockerfile", "Django на порту 8000; ожидание БД и migrate при старте, depends_on: service_healthy"],
        ],
        "Таблица 3 – Сервисы Docker Compose",
    )
    h2(doc, "3.6 Разработанный MCP-сервер")
    para(
        doc,
        "MCP-сервер (mcp_server/server.py, Python, MCP SDK 2.x, транспорт "
        "stdio) поднимает настройки Django, подключается к PostgreSQL "
        "на адресе 127.0.0.1:5432 (порт публикуется контейнером db) "
        "и предоставляет агенту инструменты из таблицы 4.",
    )
    table(
        doc,
        ["Инструмент", "Назначение"],
        [
            ["list_exams", "перечень экзаменов с количеством вопросов и попыток"],
            ["get_exam", "данные одного экзамена по slug и его попытки"],
            ["list_questions", "вопросы экзамена с вариантами и ключом ответов"],
            ["exam_stats", "средний балл, число попыток, доля успешных сдач"],
            ["get_attempt", "детализация попытки: все ответы и их корректность"],
            ["get_db_schema", "схема таблиц БД из information_schema"],
            ["list_users", "пользователи и статистика их попыток"],
        ],
        "Таблица 4 – Инструменты разработанного MCP-сервера",
    )
    h2(doc, "3.7 Конфигурация AI-агента")
    para(
        doc,
        "В корне проекта размещены материалы для работы агентов: AGENTS.md "
        "с картой проекта, командами Docker, описанием модели данных "
        "и соглашениями; .opencode/skills/exam-prep-dev/SKILL.md – "
        "пользовательский Skill с чек-листами типовых изменений (новый тип "
        "вопроса, потоки представлений, флешкарты, миграции, сидирование); "
        "opencode.json – конфигурация, подключающая MCP-сервер exam-db "
        "и включающая AGENTS.md в инструкции агента. Все файлы проверены "
        "загрузкой opencode: агент видит Skill и инструкции и успешно "
        "вызывает инструменты MCP.",
    )

    # 4 РЕЗУЛЬТАТЫ
    h1(doc, "4 Результаты и их обсуждение")
    para(
        doc,
        "Приёмочная выполнялась на чистом окружении: docker compose down -v, "
        "затем docker compose up --build. Результаты проверки приведены "
        "в таблице 5.",
    )
    table(
        doc,
        ["Проверка", "Результат"],
        [
            ["Запуск docker compose up --build (тома удалены)", "db и web запущены, статус healthy, миграции применены автоматически"],
            ["Сидирование данных", "создано 3 экзамена (13 вопросов) и 2 колоды (16 карточек); повторный запуск – пропуск"],
            ["Модульные и интеграционные тесты", "23 теста – OK (exams: 12, flashcards: 11)"],
            ["HTTP-страницы (списки, описание, стили)", "код 200; анонимный доступ к сдаче/изучению – 302 на страницу входа"],
            ["Сценарий студента: экзамен", "7/7 баллов (100 %), статус «passed», результат в истории попыток"],
            ["Сценарий студента: колода", "сессия изучения завершена, результат 5/8 сохранён и отображается"],
            ["Административная панель", "вход суперпользователя, разделы экзаменов, вопросов, колод доступны"],
            ["MCP-сервер (stdio, с хоста)", "7 инструментов перечислены, вызов exam_stats возвращает данные БД"],
            ["Загрузка конфигурации opencode", "Skill exam-prep-dev, AGENTS.md и MCP exam-db подключены; агент выполняет вызовы инструментов"],
        ],
        "Таблица 5 – Результаты приёмочной проверки",
    )
    para(
        doc,
        "Проверка подтвердила, что приложение полностью работает в составе "
        "Docker Compose: единственный компонент вне контейнеров – MCP-сервер, "
        "который по замыслу запускается на хосте самим opencode "
        "(виртуальное окружение .venv-mcp) и обращается к опубликованному "
        "порту PostgreSQL. Выявленные в ходе разработки дефекты (ошибка "
        "в данных сидирования, несоответствие в тесте, отсутствие права "
        "исполнения у entrypoint-скрипта при монтировании каталога) "
        "устранены и покрыты тестами.",
    )

    # ЗАКЛЮЧЕНИЕ
    h1(doc, "Заключение", page_break=True)
    para(
        doc,
        "В ходе работы разработано и проверено веб-приложение для подготовки "
        "к экзаменам «ExamPrep» на Django и PostgreSQL, целиком запускаемое "
        "средствами Docker Compose. Реализованы два сценария запоминания "
        "– экзамен с объективной автоматической проверкой и таймером "
        "и карточки с самооценкой; обеспечено администрирование контента "
        "через Django admin, учёт результатов и разрешение доступа "
        "к персональным данным.",
    )
    para(
        doc,
        "Сформированы требования к работе с кодовой базой для AI-агентов: "
        "инструкция AGENTS.md, пользовательский Skill «exam-prep-dev» "
        "и конфигурация opencode.json; разработан собственный MCP-сервер, "
        "предоставляющий агенту семь инструментов доступа к данным "
        "и схеме БД. Все компоненты интегрированы и проверены в составе "
        "единого окружения. Тестовый набор из 23 тестов выполняется без "
        "ошибок; приёмочная проверка по ключевым сценариям пройдена.",
    )
    para(
        doc,
        "В качестве направлений дальнейшего развития могут быть названы: "
        "ролевая модель (преподаватель/студент) с публикацией экзаменов, "
        "генерация вопросов средствами ИИ, импорт колод, развитие REST API "
        "на основе Django REST Framework, перевод интерфейса, а также "
        "продакшн-конфигурация (Gunicorn, Nginx, отдельный сервис статики).",
    )

    # БИБЛИОГРАФИЯ
    h1(doc, "Библиографический список")
    refs = [
        "ГОСТ 7.32–2017. Отчёт о научно-исследовательской работе. Структура "
        "и правила оформления : национальный стандарт Российской Федерации. "
        "– Введ. 2017-11-11. – Москва : Стандартинформ, 2017. – 14 с.",
        "ГОСТ Р 7.0.100–2018. Библиографические ссылки : национальный "
        "стандарт Российской Федерации. – Введ. 2019-07-01. – Москва : "
        "Стандартинформ, 2018. – 16 с.",
        "Django Documentation [Электронный ресурс]. – Режим доступа : "
        "https://docs.djangoproject.com/ (дата обращения : 18.10.2026).",
        "PostgreSQL 16 Documentation [Электронный ресурс]. – Режим доступа : "
        "https://www.postgresql.org/docs/16/ (дата обращения : 18.10.2026).",
        "Docker Documentation [Электронный ресурс]. – Режим доступа : "
        "https://docs.docker.com/ (дата обращения : 18.10.2026).",
        "Docker Compose Documentation [Электронный ресурс]. – Режим доступа : "
        "https://docs.docker.com/compose/ (дата обращения : 18.10.2026).",
        "Model Context Protocol Specification [Электронный ресурс]. – Режим "
        "доступа : https://modelcontextprotocol.io/ (дата обращения : "
        "18.10.2026).",
        "opencode Documentation [Электронный ресурс]. – Режим доступа : "
        "https://opencode.ai/ (дата обращения : 18.10.2026).",
        "The Python Language Reference [Электронный ресурс]. – Режим доступа : "
        "https://docs.python.org/3/reference/ (дата обращения : 18.10.2026).",
        "psycopg – PostgreSQL adapter for Python [Электронный ресурс]. – Режим "
        "доступа : https://www.psycopg.org/ (дата обращения : 18.10.2026).",
    ]
    for i, r in enumerate(refs, 1):
        p = para(doc, f"[{i}] {r}", indent=0)
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.first_line_indent = Cm(-1.25)

    # ПРИЛОЖЕНИЯ
    h1(doc, "ПРИЛОЖЕНИЕ А", page_break=True)
    para(doc, "Структура репозитория проекта", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=True)
    code(
        doc,
        [
            "django_project/",
            "├── AGENTS.md                     # инструкция для AI-агента",
            "├── README.md                     # описание проекта",
            "├── opencode.json                 # конфигурация opencode (MCP, инструкции)",
            "├── .opencode/skills/exam-prep-dev/SKILL.md   # Skill агента",
            "├── docker-compose.yml            # сервисы db и web",
            "├── Dockerfile                    # образ приложения",
            "├── entrypoint.sh                 # ожидание БД + миграции",
            "├── requirements.txt              # Django, psycopg",
            "├── config/                       # settings.py, urls.py, wsgi.py",
            "├── exams/                        # приложение экзаменов",
            "│   ├── models.py                 # Exam, Question, Choice, Attempt, Answer",
            "│   ├── views.py, urls.py, admin.py",
            "│   ├── tests.py                  # 12 тестов",
            "│   ├── migrations/0001_initial.py",
            "│   └── management/commands/seed_exams.py",
            "├── flashcards/                   # приложение карточек",
            "│   ├── models.py                 # Deck, Card, DeckResult",
            "│   ├── views.py, urls.py, admin.py",
            "│   ├── tests.py                  # 11 тестов",
            "│   ├── migrations/0001_initial.py",
            "│   └── management/commands/seed_flashcards.py",
            "├── mcp_server/server.py          # MCP-сервер (7 инструментов)",
            "├── templates/                    # base.html, registration/",
            "│   ├── exams/                    # шаблоны экзаменов",
            "│   └── flashcards/               # шаблоны колод",
            "├── static/css/style.css          # оформление",
            "└── report/                       # настоящий отчёт",
        ],
    )

    h1(doc, "ПРИЛОЖЕНИЕ Б", page_break=True)
    para(doc, "Команды развёртывания и сопровождения", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=True)
    code(
        doc,
        [
            "# первичный запуск (сборка, миграции, ожидание БД)",
            "docker compose up --build",
            "",
            "# наполнение демо-данными (идемпотентно)",
            "docker compose exec web python manage.py seed_exams",
            "docker compose exec web python manage.py seed_flashcards",
            "",
            "# тесты (23) и рабочий shell",
            "docker compose exec web python manage.py test",
            "docker compose exec web python manage.py shell",
            "",
            "# управление контейнерами",
            "docker compose ps        # состояние сервисов",
            "docker compose logs -f web",
            "docker compose down      # остановить (том сохраняется)",
            "docker compose down -v   # остановить с удалением данных",
            "",
            "# MCP-сервер на хосте (для opencode)",
            "python3 -m venv .venv-mcp",
            ".venv-mcp/bin/pip install -r requirements.txt mcp",
            ".venv-mcp/bin/python mcp_server/server.py",
            "",
            "# запуск агента выполняется из корня проекта",
            "cd django_project && opencode",
        ],
    )

    h1(doc, "ПРИЛОЖЕНИЕ В", page_break=True)
    para(doc, "Фрагмент конфигурации opencode.json", align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, bold=True)
    code(
        doc,
        [
            "{",
            '  "$schema": "https://opencode.ai/config.json",',
            '  "instructions": ["AGENTS.md"],',
            '  "mcp": {',
            '    "exam-db": {',
            '      "type": "local",',
            '      "command": [".venv-mcp/bin/python", "mcp_server/server.py"],',
            '      "enabled": true,',
            '      "environment": {',
            '        "DJANGO_SETTINGS_MODULE": "config.settings",',
            '        "DB_HOST": "127.0.0.1",',
            '        "DB_PORT": "5432"',
            "      }",
            "    }",
            "  }",
            "}",
        ],
    )
    para(doc, "", indent=0)
    para(
        doc,
        "Skill агента размещён по пути .opencode/skills/exam-prep-dev/SKILL.md "
        "и содержит фронтматтер name/description и разделы с чек-листами "
        "развития проекта.",
        indent=0,
    )

    doc.core_properties.title = "Отчёт по лабораторной работе"
    doc.core_properties.subject = "Веб-приложение для подготовки к экзаменам"
    doc.save(OUT)
    print(f"saved: {OUT}")


def tbl_count():
    return TBL


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=16)
    build(ap.parse_args().pages)
