const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageOrientation, VerticalAlign
} = require('docx');
const fs = require('fs');

const GRAY_LIGHT = "F2F2F2";
const BLUE_LIGHT = "D9E8F5";
const BLUE_MID   = "2E6DA4";
const WHITE      = "FFFFFF";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160 },
    children: [new TextRun({ text, bold: true, size: 32, font: "Arial", color: "1F3864" })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 26, font: "Arial", color: "2E6DA4" })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 180, after: 80 },
    children: [new TextRun({ text, bold: true, size: 22, font: "Arial", color: "404040" })]
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 20, font: "Arial", ...opts })]
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 20, font: "Arial" })]
  });
}

function cell(text, opts = {}) {
  const { bold = false, shade = WHITE, width = 2000, color = "000000" } = opts;
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      children: [new TextRun({ text, bold, size: 18, font: "Arial", color })]
    })]
  });
}

function headerCell(text, width = 2000) {
  return cell(text, { bold: true, shade: BLUE_LIGHT, width, color: "1F3864" });
}

function sectionCell(text, totalWidth = 9360) {
  return new TableCell({
    borders,
    columnSpan: 3,
    width: { size: totalWidth, type: WidthType.DXA },
    shading: { fill: GRAY_LIGHT, type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, size: 18, font: "Arial", color: "404040" })]
    })]
  });
}

function tableRow(cols) {
  return new TableRow({ children: cols });
}

function spacer() {
  return new Paragraph({ spacing: { before: 100, after: 100 }, children: [new TextRun("")] });
}

// ─── Таблица: структура позиции каталога ─────────────────────────────────────
const catalogFieldsTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3200, 2560, 3600],
  rows: [
    tableRow([headerCell("Поле", 3200), headerCell("Источник", 2560), headerCell("Примечание", 3600)]),
    tableRow([cell("Код (8 знаков)", { width: 3200 }), cell("Генерируется системой", { width: 2560 }), cell("Уникальный, не начинается на 0", { width: 3600 })]),
    tableRow([cell("Наименование + краткое описание", { width: 3200 }), cell("Составляется системой", { width: 2560 }), cell("Одно поле. Нормализованное название с характеристиками", { width: 3600 })]),
    tableRow([cell("Подробное описание", { width: 3200 }), cell("Из прайса поставщика", { width: 2560 }), cell("Берётся от поставщика", { width: 3600 })]),
    tableRow([cell("Наша цена", { width: 3200 }), cell("Рассчитывается автоматически", { width: 2560 }), cell("По правилу приоритета наличия (см. раздел 5)", { width: 3600 })]),
    tableRow([cell("РРЦ", { width: 3200 }), cell("Из прайса / вручную", { width: 2560 }), cell("Рекомендованная розничная цена, часто пустая", { width: 3600 })]),
    tableRow([cell("Гарантия", { width: 3200 }), cell("Из прайса поставщика", { width: 2560 }), cell("Берётся максимальная среди всех поставщиков", { width: 3600 })]),
    tableRow([cell("Ссылка на товар у производителя", { width: 3200 }), cell("Из прайса / поиск", { width: 2560 }), cell("Ссылка на конкретную страницу товара на сайте производителя", { width: 3600 })]),
    tableRow([cell("Производитель", { width: 3200 }), cell("Из прайса поставщика", { width: 2560 }), cell("", { width: 3600 })]),
    tableRow([cell("Артикул", { width: 3200 }), cell("Из прайса поставщика", { width: 2560 }), cell("Разные артикулы = разные товары", { width: 3600 })]),
    tableRow([cell("EAN / UPC", { width: 3200 }), cell("Из прайса поставщика", { width: 2560 }), cell("Разные EAN = тот же товар (если нет исключений)", { width: 3600 })]),
    tableRow([cell("Страна происхождения", { width: 3200 }), cell("Из прайса поставщика", { width: 2560 }), cell("Заполняется если доступна", { width: 3600 })]),
    tableRow([cell("Категория", { width: 3200 }), cell("Определяется системой / ИИ", { width: 2560 }), cell("По категории у поставщика при спорных случаях", { width: 3600 })]),
    tableRow([cell("Дата создания", { width: 3200 }), cell("Автоматически", { width: 2560 }), cell("", { width: 3600 })]),
    tableRow([cell("Дата последнего обновления", { width: 3200 }), cell("Автоматически", { width: 2560 }), cell("", { width: 3600 })]),
  ]
});

// ─── Таблица: позиция поставщика ─────────────────────────────────────────────
const supplierFieldsTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3200, 2560, 3600],
  rows: [
    tableRow([headerCell("Поле", 3200), headerCell("Источник", 2560), headerCell("Примечание", 3600)]),
    tableRow([cell("Ссылка на поставщика", { width: 3200 }), cell("Справочник поставщиков", { width: 2560 }), cell("", { width: 3600 })]),
    tableRow([cell("Ссылка на товар в нашем каталоге", { width: 3200 }), cell("После первичного сопоставления", { width: 2560 }), cell("После первого сопоставления — только по коду поставщика", { width: 3600 })]),
    tableRow([cell("Код товара у поставщика", { width: 3200 }), cell("Из прайса", { width: 2560 }), cell("", { width: 3600 })]),
    tableRow([cell("Цена (оригинальная)", { width: 3200 }), cell("Из прайса", { width: 2560 }), cell("В валюте и с НДС/без НДС как есть у поставщика", { width: 3600 })]),
    tableRow([cell("Цена (пересчитанная)", { width: 3200 }), cell("Рассчитывается", { width: 2560 }), cell("По правилу поставщика (валюта, НДС)", { width: 3600 })]),
    tableRow([cell("Наличие", { width: 3200 }), cell("Из прайса", { width: 2560 }), cell("в наличии / под заказ / в резерве / скоро на складе (транзит)", { width: 3600 })]),
    tableRow([cell("Количество", { width: 3200 }), cell("Из прайса", { width: 2560 }), cell("Точное или примерное", { width: 3600 })]),
    tableRow([cell("Гарантия", { width: 3200 }), cell("Из прайса", { width: 2560 }), cell("Гарантия от данного поставщика", { width: 3600 })]),
    tableRow([cell("Дата обновления", { width: 3200 }), cell("Автоматически", { width: 2560 }), cell("При каждом получении нового прайса", { width: 3600 })]),
    tableRow([cell("История цен", { width: 3200 }), cell("Автоматически", { width: 2560 }), cell("Скрытая, хранится для отслеживания динамики", { width: 3600 })]),
  ]
});

// ─── Таблица: структура выгрузки ─────────────────────────────────────────────
const exportTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [600, 600, 1000, 2200, 1560, 1200, 1200],
  rows: [
    tableRow([
      headerCell("Кол.", 600), headerCell("Кол.", 600),
      headerCell("Кол.", 1000), headerCell("Кол.", 2200),
      headerCell("Кол.", 1560), headerCell("Кол.", 1200), headerCell("Кол.", 1200)
    ]),
    tableRow([
      cell("1", { shade: GRAY_LIGHT, width: 600 }), cell("2", { shade: GRAY_LIGHT, width: 600 }),
      cell("3", { width: 1000 }), cell("4", { width: 2200 }),
      cell("5", { width: 1560 }), cell("6", { width: 1200 }), cell("7...", { width: 1200 })
    ]),
    tableRow([
      cell("Резерв", { shade: GRAY_LIGHT, width: 600 }), cell("Резерв", { shade: GRAY_LIGHT, width: 600 }),
      cell("Код", { shade: BLUE_LIGHT, bold: true, width: 1000 }),
      cell("Наименование + описание", { shade: BLUE_LIGHT, bold: true, width: 2200 }),
      cell("Подробное описание", { shade: BLUE_LIGHT, bold: true, width: 1560 }),
      cell("Наша цена", { shade: BLUE_LIGHT, bold: true, width: 1200 }),
      cell("РРЦ", { shade: BLUE_LIGHT, bold: true, width: 1200 }),
    ]),
  ]
});

// ─── Таблица: колонки 8-12 + поставщики ──────────────────────────────────────
const exportTable2 = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [800, 1560, 1200, 1400, 1100, 1100, 1100, 1100],
  rows: [
    tableRow([
      headerCell("8", 800), headerCell("9", 1560),
      headerCell("10", 1200), headerCell("11", 1400),
      headerCell("12", 1100), headerCell("П1×2", 1100),
      headerCell("П2×2", 1100), headerCell("П3...×2", 1100),
    ]),
    tableRow([
      cell("Гарантия", { shade: BLUE_LIGHT, bold: true, width: 800 }),
      cell("Ссылка на товар у производителя", { shade: BLUE_LIGHT, bold: true, width: 1560 }),
      cell("Производитель", { shade: BLUE_LIGHT, bold: true, width: 1200 }),
      cell("Артикул", { shade: BLUE_LIGHT, bold: true, width: 1400 }),
      cell("EAN / UPC", { shade: BLUE_LIGHT, bold: true, width: 1100 }),
      cell("Цена / Наличие", { shade: "E8F5E9", bold: true, width: 1100 }),
      cell("Цена / Наличие", { shade: "E8F5E9", bold: true, width: 1100 }),
      cell("Цена / Наличие ...", { shade: "E8F5E9", bold: true, width: 1100 }),
    ]),
  ]
});

// ─── Таблица: правило расчёта нашей цены ─────────────────────────────────────
const priceRuleTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [720, 2640, 6000],
  rows: [
    tableRow([headerCell("Шаг", 720), headerCell("Условие", 2640), headerCell("Действие", 6000)]),
    tableRow([cell("1", { width: 720 }), cell("Есть «в наличии»", { width: 2640 }), cell("Минимальная цена среди поставщиков со статусом «в наличии»", { width: 6000 })]),
    tableRow([cell("2", { width: 720 }), cell("Нет наличия, есть «резерв»", { width: 2640 }), cell("Минимальная цена среди поставщиков со статусом «резерв»", { width: 6000 })]),
    tableRow([cell("3", { width: 720 }), cell("Нет резерва, есть «под заказ»", { width: 2640 }), cell("Минимальная цена среди поставщиков со статусом «под заказ»", { width: 6000 })]),
    tableRow([cell("4", { width: 720 }), cell("Нет под заказ, есть «транзит»", { width: 2640 }), cell("Минимальная цена среди поставщиков со статусом «транзит»", { width: 6000 })]),
    tableRow([cell("5", { width: 720 }), cell("Нигде нет", { width: 2640 }), cell("Позиция скрывается из выгрузки полностью", { width: 6000 })]),
  ]
});

// ─── Таблица: правила сопоставления ──────────────────────────────────────────
const matchingRulesTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3600, 2160, 3600],
  rows: [
    tableRow([headerCell("Правило", 3600), headerCell("Результат", 2160), headerCell("Примечание", 3600)]),
    tableRow([cell("Разные артикулы", { width: 3600 }), cell("Разные товары", { bold: true, width: 2160 }), cell("Даже если характеристики идентичны", { width: 3600 })]),
    tableRow([cell("Разные EAN / UPC", { width: 3600 }), cell("Тот же товар", { width: 2160 }), cell("Если нет явного исключения в настройках", { width: 3600 })]),
    tableRow([cell("Разная гарантия у поставщиков", { width: 3600 }), cell("Тот же товар", { width: 2160 }), cell("В каталог записывается максимальная гарантия", { width: 3600 })]),
    tableRow([cell("Retail = RTL = RET = BOX", { width: 3600 }), cell("Одна группа", { width: 2160 }), cell("Тип поставки «розничная», при сравнении равнозначны", { width: 3600 })]),
    tableRow([cell("OEM", { width: 3600 }), cell("Отдельная группа", { width: 2160 }), cell("Всегда отдельный товар от Retail-версии", { width: 3600 })]),
    tableRow([cell("Тип поставки не указан", { width: 3600 }), cell("По большинству", { width: 2160 }), cell("Если большинство источников = RTL, считаем RTL", { width: 3600 })]),
    tableRow([cell("После первого сопоставления", { width: 3600 }), cell("По коду", { width: 2160 }), cell("Повторный ИИ-анализ не нужен. Код поставщика = постоянная привязка", { width: 3600 })]),
  ]
});

// ─── Таблица: иерархия каталога ──────────────────────────────────────────────
const hierarchyTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 2400, 2400, 2160],
  rows: [
    tableRow([headerCell("Категория", 2400), headerCell("Производитель", 2400), headerCell("Модель (деление)", 2400), headerCell("Сортировка", 2160)]),
    tableRow([cell("Видеокарты", { width: 2400 }), cell("MSI, Gigabyte...", { width: 2400 }), cell("По серии GPU (RTX 5070, RTX 5080...)", { width: 2400 }), cell("От дешёвой к дорогой", { width: 2160 })]),
    tableRow([cell("Материнские платы", { width: 2400 }), cell("MSI, Gigabyte...", { width: 2400 }), cell("По чипсету (B860, Z890...)", { width: 2400 }), cell("От дешёвой к дорогой", { width: 2160 })]),
    tableRow([cell("SSD", { width: 2400 }), cell("WD, Samsung...", { width: 2400 }), cell("По объёму (1TB, 2TB...)", { width: 2400 }), cell("От дешёвой к дорогой", { width: 2160 })]),
    tableRow([cell("Прочие группы", { width: 2400 }), cell("По производителю", { width: 2400 }), cell("Без особого деления (ИИ подскажет)", { width: 2400 }), cell("От дешёвой к дорогой", { width: 2160 })]),
  ]
});

// ─── Таблица: архитектура ИИ ──────────────────────────────────────────────────
const aiTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 3360, 3600],
  rows: [
    tableRow([headerCell("Уровень", 2400), headerCell("Что делает", 3360), headerCell("Когда используется", 3600)]),
    tableRow([cell("1. Правила", { width: 2400 }), cell("Нормализация: регистр, синонимы типа поставки, известные сокращения", { width: 3360 }), cell("Всегда, первый шаг", { width: 3600 })]),
    tableRow([cell("2. Сравнение по атрибутам", { width: 2400 }), cell("Сопоставление по артикулу, EAN, названию модели", { width: 3360 }), cell("После нормализации", { width: 3600 })]),
    tableRow([cell("3. ИИ без интернета", { width: 2400 }), cell("Семантическое сравнение названий (эмбеддинги)", { width: 3360 }), cell("Когда правила не дали однозначного ответа", { width: 3600 })]),
    tableRow([cell("4. ИИ + интернет", { width: 2400 }), cell("Поиск товара на сайте производителя, проверка спорных случаев", { width: 3360 }), cell("Только для новых неизвестных суффиксов и конфликтов", { width: 3600 })]),
  ]
});

// ─── Документ ─────────────────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F3864" },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E6DA4" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: "404040" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1080, hanging: 360 } } } },
        ]
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    children: [

      // ── Титул ───────────────────────────────────────────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 480, after: 120 },
        children: [new TextRun({ text: "Техническое задание", bold: true, size: 40, font: "Arial", color: "1F3864" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "Система управления товарным каталогом", bold: true, size: 28, font: "Arial", color: "2E6DA4" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 480 },
        children: [new TextRun({ text: "Версия 1.0  —  Май 2026", size: 20, font: "Arial", color: "808080" })]
      }),

      // ── 1. Назначение ────────────────────────────────────────────────────────
      h1("1. Назначение системы"),
      p("Система предназначена для автоматического сбора, нормализации и сопоставления товаров из прайс-листов множества поставщиков (десятки источников) с целью формирования единого внутреннего товарного каталога. Каталог используется для управления ценами, наличием и информацией о товарах."),
      spacer(),

      // ── 2. Структура каталога ────────────────────────────────────────────────
      h1("2. Структура товарного каталога"),

      h2("2.1. Иерархия каталога"),
      p("Каталог организован по следующей иерархии (визуальное разделение, не отдельные строки в выгрузке):"),
      bullet("Категория (например: Видеокарты, Материнские платы, SSD, Процессоры...)"),
      bullet("Производитель (MSI, Gigabyte, WD...)"),
      bullet("Модель — деление зависит от категории (см. таблицу ниже)"),
      bullet("Внутри модели — сортировка от дешёвой позиции к дорогой"),
      spacer(),
      hierarchyTable,
      spacer(),
      p("Для спорных категорий (например, Thunderbolt dock — периферия или сеть) — определяем принадлежность по тому, в какой группе товар находится у поставщиков."),
      spacer(),

      h2("2.2. Поля карточки товара в каталоге"),
      catalogFieldsTable,
      spacer(),

      // ── 3. Структура выгрузки ────────────────────────────────────────────────
      h1("3. Структура выгрузки (таблица)"),
      p("Каталог можно выгрузить в табличный формат. Колонки расположены в следующем порядке:"),
      spacer(),
      exportTable,
      spacer(),
      exportTable2,
      spacer(),
      p("Примечания по выгрузке:"),
      bullet("Колонки 1 и 2 — зарезервированы, пустые, назначение определяется в будущем"),
      bullet("Колонки 13 и далее — по 2 колонки на каждого поставщика: Цена и Наличие. Поставщики именуются П1, П2, П3... с возможностью задать имя и формулу расчёта цены"),
      bullet("Строки-разделители (Категория → Производитель → Модель) — только визуальная группировка, не отдельные строки в выгрузке"),
      bullet("Позиции, которых нет ни у одного поставщика — в выгрузку не включаются"),
      spacer(),

      // ── 4. Поставщики ───────────────────────────────────────────────────────
      h1("4. Работа с поставщиками"),

      h2("4.1. Карточка поставщика"),
      p("Для каждого поставщика один раз задаётся:"),
      bullet("Название поставщика"),
      bullet("Правило расчёта цены: валюта (RUB / USD / EUR), признак НДС (включён / не включён), курс пересчёта если нужен"),
      bullet("Формат прайса (структура файла)"),
      spacer(),

      h2("4.2. Поля позиции поставщика"),
      supplierFieldsTable,
      spacer(),

      h2("4.3. Статусы наличия"),
      p("Возможные статусы (в порядке приоритета для расчёта нашей цены):"),
      bullet("в наличии"),
      bullet("в резерве"),
      bullet("под заказ"),
      bullet("скоро на складе (транзит)"),
      spacer(),

      // ── 5. Расчёт нашей цены ────────────────────────────────────────────────
      h1("5. Правило расчёта «нашей цены»"),
      p("Цена определяется автоматически по приоритету статуса наличия:"),
      spacer(),
      priceRuleTable,
      spacer(),
      p("Позиция полностью скрывается из выгрузки если ни у одного поставщика нет товара ни в каком статусе."),
      spacer(),

      // ── 6. Сопоставление товаров ────────────────────────────────────────────
      h1("6. Правила сопоставления товаров"),

      h2("6.1. Основные правила"),
      matchingRulesTable,
      spacer(),

      h2("6.2. Тип поставки"),
      p("Тип поставки является частью идентификации товара. Товары с разным типом поставки считаются разными позициями в каталоге:"),
      bullet("Retail / RTL / RET / BOX — одна группа (розничная поставка)"),
      bullet("OEM — отдельная группа"),
      bullet("Если тип поставки не указан у одного поставщика, но указан у большинства других — берём по большинству"),
      bullet("Если тип поставки неизвестен и не поддаётся определению — помечается как «не определён»"),
      spacer(),

      h2("6.3. Архитектура ИИ-сопоставления (правила + ИИ)"),
      p("Система работает по принципу «сначала дешёвые правила, потом дорогой ИИ»:"),
      spacer(),
      aiTable,
      spacer(),
      p("ИИ с поиском в интернете подключается только для:"),
      bullet("Неизвестных суффиксов которых нет в словаре системы"),
      bullet("Конфликтов (у большинства RTL, у одного явно OEM)"),
      bullet("Новых товаров без аналогов в других источниках"),
      spacer(),
      p("Система накапливает базу знаний — чем больше прайсов обработано, тем реже нужен интернет."),
      spacer(),

      // ── 7. Первичное и повторное сопоставление ──────────────────────────────
      h1("7. Первичное и повторное сопоставление"),
      bullet("Первичное сопоставление: ИИ анализирует название, артикул, EAN и определяет соответствие товара в прайсе поставщика позиции в нашем каталоге"),
      bullet("После первого подтверждённого сопоставления — привязка фиксируется. Далее при получении нового прайса от этого поставщика сопоставление идёт только по коду поставщика"),
      bullet("Предполагается что у поставщика под одним кодом не может появиться другой товар"),
      spacer(),

      // ── 8. Хранение истории ─────────────────────────────────────────────────
      h1("8. История изменений"),
      bullet("История изменения цен от каждого поставщика хранится в скрытом виде"),
      bullet("Количество хранимых обновлений от каждого поставщика определяется настройками"),
      bullet("При поступлении нового прайса цены обновляются, предыдущие данные сохраняются"),
      bullet("История изменений полей карточки товара — предусмотреть возможность хранения, по умолчанию не ведётся"),
      spacer(),

      // ── 9. Будущие доработки ─────────────────────────────────────────────────
      h1("9. Планируемые доработки"),
      bullet("Для каждой группы товаров — отдельные поля характеристик (для удобства поиска на сайтах)"),
      bullet("Автоматический поиск и заполнение ссылки на товар у производителя по отдельной команде"),
      bullet("Статус «снят с производства» (не нужен на первом этапе)"),
      bullet("Настройка срока хранения истории цен по каждому поставщику"),
      spacer(),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/claude/tz_catalog.docx', buf);
  console.log('Done');
});
