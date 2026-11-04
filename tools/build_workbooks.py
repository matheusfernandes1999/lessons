#!/usr/bin/env python3
"""Gera lessons/*.json e index.json dos tópicos importados de apostilas da plataforma.

Uso:
    python3 tools/build_workbooks.py                       # todos os tópicos importados
    python3 tools/build_workbooks.py pt/essentials

Formatos (campo `sourceFormat` do topic.json):
    html            source/manifest.json + source/*.html  -> Tiptap (tools/html_to_tiptap.py)
    workbook-json   source/*.json (uma lição por arquivo) -> Tiptap com quizzes (abaixo)

Os tópicos escritos em Markdown (sem `sourceFormat`) continuam em tools/build_lessons.py.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lessons import SourceError, parse_quiz  # noqa: E402
from html_to_tiptap import html_to_doc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ["speaking", "vocabulary", "listening", "reading", "writing"]


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


# ------------------------------------------------------------------ helpers Tiptap

def text(value, *marks):
    node = {"type": "text", "text": value}
    if marks:
        node["marks"] = [{"type": m} for m in marks]
    return node


def para(*parts):
    """Parágrafo: strings simples ou (texto, 'bold'/'italic') para marcas."""
    nodes = []
    for part in parts:
        if isinstance(part, tuple):
            value, *marks = part
        else:
            value, marks = part, ()
        if value:
            nodes.append(text(value, *marks))
    return {"type": "paragraph", "content": nodes} if nodes else {"type": "paragraph"}


def heading(level, value):
    return {"type": "heading", "attrs": {"level": level}, "content": [text(value)]}


def bullets(items):
    return {"type": "bulletList", "content": [
        {"type": "listItem", "content": [item if isinstance(item, dict) else para(item)]} for item in items]}


def numbered(items):
    return {"type": "orderedList", "attrs": {"start": 1}, "content": [
        {"type": "listItem", "content": [item if isinstance(item, dict) else para(item)]} for item in items]}


def quote(value):
    return {"type": "blockquote", "content": [para(value)]}


def table(header, rows):
    def cell(kind, value):
        return {"type": kind, "attrs": {"colspan": 1, "rowspan": 1, "colwidth": None}, "content": [para(value)]}

    return {"type": "table", "content": [
        {"type": "tableRow", "content": [cell("tableHeader", h) for h in header]},
        *({"type": "tableRow", "content": [cell("tableCell", c) for c in row]} for row in rows),
    ]}


def pair(first, second):
    return para((first, "bold"), " — ", second)


def label(name, value):
    return para((f"{name}: ", "bold"), value)


def pretty_key(key):
    """'A_multiple_choice' -> 'A · Multiple choice'."""
    head, _, rest = key.partition("_")
    return f"{head} · {rest.replace('_', ' ').capitalize()}" if rest else key


def quiz(lesson_key, name, mc_items, mc_answers, gap_items, gap_answers, where):
    """Nó quiz (mesmo formato dos demais tópicos) via parse_quiz do build_lessons."""
    lines = []
    for item, answer in zip(mc_items, mc_answers):
        lines.append(f"? mc|grammar|{item['prompt']}")
        for letter, option in item["options"].items():
            lines.append(f"{'*' if letter == answer['answer'] else ''}{letter}) {option}")
        lines.append(f"= {answer['sentence']}")
    for item, answer in zip(gap_items, gap_answers):
        lines.append(f"? w|grammar|{item['sentence']} ({item['hint']})")
        lines.append(f"> {answer['answer']}")
        lines.append(f"= {answer['full_sentence']}")
    return parse_quiz(lines, f"quiz_{lesson_key}_{name}", where)


# ------------------------------------------------------------------ workbook-json -> Tiptap

def workbook_doc(l, lesson_key, where):
    s, t = l["student"], l["teacher"]
    key, p1, p2, hw = t["answer_key"], s["practice_1"], s["practice_2"], s["your_homework"]
    review = s["review"]
    doc = []

    doc += [
        heading(2, "Lesson objective"),
        label("Module", l["module"]),
        label("Level", l["level"]),
        label("Main grammar", l["main_grammar"]),
        label("Previous knowledge", l["previous_knowledge"]),
        label("Key vocabulary", ", ".join(l["key_vocabulary"])),
        label("Lesson task", s["lets_begin"]),
    ]

    doc += [
        heading(2, "1. Let's begin and explanation (5 min)"),
        label("Basic rule", s["basic_rule"]),
        label("Structure", s["structure"]),
        label("English comparison", s["english_comparison"]),
        heading(3, "Model sentences"),
        bullets([pair(m["pt"], m["en"]) for m in s["model_sentences"]]),
        heading(3, "Useful words"),
        table(["Term", "Meaning", "Example"], [[w["term"], w["meaning"], w["example"]] for w in s["useful_words"]]),
    ]

    mc, gap = p1["multiple_choice"], p1["gap_fill"]
    reading = p1["mini_reading"]
    doc += [
        heading(2, "2. Practice 1 (9 min)"),
        heading(3, "Multiple choice and gap fill"),
        para((mc["instruction"], "italic")),
        para((gap["instruction"], "italic")),
        quiz(lesson_key, "practice1", mc["items"], key["practice_1"]["multiple_choice"],
             gap["items"], key["practice_1"]["gap_fill"], f"{where} [practice1]"),
        heading(3, "Mini reading"),
        para((reading["instruction"], "italic")),
        quote(reading["text"]),
        numbered(reading["questions"]),
        heading(3, "Speaking practice"),
        para((p1["speaking_practice"]["instruction"], "italic")),
        numbered(p1["speaking_practice"]["questions"]),
    ]

    drill = review["oral_substitution_drill"]
    doc += [
        heading(2, "3. Review (5 min)"),
        label("Another way to understand it", review["another_way_to_understand_it"]),
        heading(3, "Examples"),
        bullets([pair(e["pt"], e["en"]) for e in review["examples"]]),
        label("Compare", review["compare"]),
        heading(3, "Common mistakes"),
        bullets([para(("✗ ", "bold"), m["wrong"], "  ", ("✓ ", "bold"), m["correct"], f" — {m['explanation']}")
                 for m in review["common_mistakes"]]),
        heading(3, "Oral substitution drill"),
        para((drill["instruction"], "italic")),
        numbered([para((i["base"], "bold"), f" → {i['cue']}") for i in drill["items"]]),
    ]

    fill = p2["fill_in"]
    listen = p2["listen_and_translate"]
    read2 = p2["reading_aloud_and_translation"]
    doc += [
        heading(2, "4. Practice 2 (10 min)"),
        heading(3, "Translate"),
        para((p2["translate"]["instruction"], "italic")),
        numbered(p2["translate"]["items"]),
        heading(3, "Fill in"),
        para((fill["instruction"], "italic")),
        quiz(lesson_key, "practice2", [], [], fill["items"], key["practice_2"]["fill_in"], f"{where} [practice2]"),
        heading(3, "Listen and translate"),
        para((listen["instruction"], "italic")),
        label("Utterances", str(listen["number_of_utterances"])),
        heading(3, "Reading aloud and translation"),
        para((read2["instruction"], "italic")),
        quote(read2["text"]),
        numbered(read2["questions"]),
    ]

    sp = s["speaking_practice"]
    doc += [
        heading(2, "5. Speaking practice (11 min)"),
        para((sp["instruction"], "italic")),
        numbered([pair(q["question"], q["english"]) for q in sp["questions"]]),
    ]

    doc.append(heading(2, "6. Homework explanation (5 min)"))
    for k, v in s["homework_explanation"].items():
        doc += [para((pretty_key(k), "bold"), f" — {v['instruction']}"),
                para(("Worked answer: ", "italic"), v["worked_answer"])]

    doc += [
        heading(2, "Homework — Your homework"),
        label("Estimated time", hw["estimated_time"]),
        para((hw["instruction"], "italic")),
        heading(3, "A and B · Choose and complete"),
        para((hw["A_multiple_choice"]["instruction"], "italic")),
        para((hw["B_gap_fill"]["instruction"], "italic")),
        quiz(lesson_key, "homework", hw["A_multiple_choice"]["items"], key["homework"]["A_multiple_choice"],
             hw["B_gap_fill"]["items"], key["homework"]["B_gap_fill"], f"{where} [homework]"),
        heading(3, "C · English to Portuguese"),
        para((hw["C_english_to_portuguese"]["instruction"], "italic")),
        numbered(hw["C_english_to_portuguese"]["items"]),
        heading(3, "D · Portuguese to English"),
        para((hw["D_portuguese_to_english"]["instruction"], "italic")),
        numbered(hw["D_portuguese_to_english"]["items"]),
        heading(3, "E · Reading"),
        para((hw["E_reading"]["instruction"], "italic")),
        quote(hw["E_reading"]["text"]),
        numbered(hw["E_reading"]["questions"]),
        heading(3, "F · Written production"),
        para(hw["F_written_production"]["instruction"] if isinstance(hw["F_written_production"], dict)
             else hw["F_written_production"]),
        heading(3, "G · Speaking"),
        para(hw["G_speaking"]["instruction"] if isinstance(hw["G_speaking"], dict) else hw["G_speaking"]),
    ]

    doc.append(heading(2, "Teacher notes"))
    if t.get("spaced_review"):
        doc.append(label("Spaced review", f"{t['spaced_review']['prompt']} → {t['spaced_review']['expected_answer']}"))
    doc.append(label("Pronunciation focus", t["pronunciation_focus"]))

    k1, k2, kh = key["practice_1"], key["practice_2"], key["homework"]
    doc += [
        heading(3, "Answer key · Practice 1"),
        label("Multiple choice", "; ".join(f"{i}. {a['answer']} ({a['sentence']})"
                                           for i, a in enumerate(k1["multiple_choice"], 1))),
        label("Gap fill", "; ".join(f"{i}. {a['full_sentence']}" for i, a in enumerate(k1["gap_fill"], 1))),
        label("Mini reading, translation", k1["mini_reading"]["translation"]),
        bullets([f"{a['question']} → {a['answer']}" for a in k1["mini_reading"]["answers"]]),
        label("Speaking models", " / ".join(k1["speaking_practice_models"])),
        heading(3, "Answer key · Review"),
        numbered([f"{d['cue']} → {d['model']}" for d in key["review"]["oral_substitution_drill"]]),
        heading(3, "Answer key · Practice 2"),
        label("Translate", "; ".join(f"{i}. {a}" for i, a in enumerate(k2["translate"], 1))),
        label("Fill in", "; ".join(f"{i}. {a['full_sentence']}" for i, a in enumerate(k2["fill_in"], 1))),
        heading(3, "Listening scripts"),
        bullets([pair(u["pt"], u["en"]) for u in k2["listen_and_translate_scripts"]]),
        label("Reading aloud, translation", k2["reading_aloud"]["translation"]),
        bullets([f"{a['question']} → {a['answer']}" for a in k2["reading_aloud"]["answers"]]),
        heading(3, "Speaking practice models"),
        numbered([para((m["question"], "bold"), f" Model: {m['model_answer']} Follow-up: {m['follow_up']} "
                       f"Watch for: {m['watch_for']}") for m in key["speaking_practice"]]),
        heading(3, "Answer key · Homework"),
        label("A · Multiple choice", "; ".join(f"{i}. {a['answer']} ({a['sentence']})"
                                                 for i, a in enumerate(kh["A_multiple_choice"], 1))),
        label("B · Gap fill", "; ".join(f"{i}. {a['full_sentence']}" for i, a in enumerate(kh["B_gap_fill"], 1))),
        label("C · English to Portuguese", "; ".join(f"{i}. {a}" for i, a in enumerate(kh["C_english_to_portuguese"], 1))),
        label("D · Portuguese to English", "; ".join(f"{i}. {a}" for i, a in enumerate(kh["D_portuguese_to_english"], 1))),
        label("E · Reading, translation", kh["E_reading"]["translation"]),
        bullets([f"{a['question']} → {a['answer']}" for a in kh["E_reading"]["answers"]]),
        label("F · Model text", kh["F_written_production"]["model_text"]),
        label("F · Assessment", kh["F_written_production"]["assessment"]),
        label("G · Speaking models", " / ".join(kh["G_speaking"]["model_answers"])),
        label("Acceptable alternatives", kh["acceptable_alternatives"]),
    ]
    return doc


# ------------------------------------------------------------------ lessons

def unit_label(unit, language):
    if language == "pt":
        return "Introdução" if unit == 0 else f"Unidade {unit}"
    return "Introduction" if unit == 0 else f"Unit {unit}"


def count_quizzes(doc):
    quizzes = [n for n in doc if n["type"] == "quiz"]
    return len(quizzes), sum(len(q["attrs"]["questions"]) for q in quizzes)


def html_lessons(topic, topic_dir):
    manifest = json.loads((topic_dir / "source" / "manifest.json").read_text(encoding="utf-8"))
    course = topic["courses"][0]["name"]
    for number, entry in enumerate(manifest, 1):
        html = (topic_dir / "source" / entry["file"]).read_text(encoding="utf-8")
        lesson_key = entry["id"].replace("-", "")
        doc = html_to_doc(html, lesson_key)
        quizzes, questions = count_quizzes(doc["content"])
        yield entry["id"], entry["title"], {
            "id": entry["id"],
            "language": topic["language"],
            "mainTopic": topic["mainTopic"],
            "course": course,
            "unit": unit_label(entry["unit"], topic["language"]),
            "lessonNumber": number,
            "title": entry["title"],
            "level": topic["level"],
            "sourceFormat": "html",
            "legacyId": entry["legacyId"],
            "quizCount": quizzes,
            "questionCount": questions,
            "content": doc,
        }


def workbook_json_lessons(topic, topic_dir):
    course = topic["courses"][0]
    for path in sorted((topic_dir / "source").glob("*.json")):
        where = str(path.relative_to(ROOT))
        l = json.loads(path.read_text(encoding="utf-8"))
        lesson_id = f"{course['code']}-{l['lesson_number']:02d}"
        lesson_key = f"{course['code']}{l['lesson_number']:02d}"
        try:
            doc = workbook_doc(l, lesson_key, where)
        except (KeyError, TypeError) as err:
            raise SourceError(f"{where}: campo ausente ou inesperado: {err!r}")
        quizzes, questions = count_quizzes(doc)
        yield lesson_id, l["title"], {
            "id": lesson_id,
            "language": topic["language"],
            "mainTopic": topic["mainTopic"],
            "course": course["name"],
            "unit": l["module"],
            "lessonNumber": l["lesson_number"],
            "title": l["title"],
            "level": l["level"],
            "durationMinutes": topic["durationMinutes"],
            "format": topic["format"],
            "focus": l["main_grammar"],
            "verifiableTask": l["student"]["lets_begin"],
            "skills": SKILLS,
            "sourceFormat": "workbook-json",
            "legacyId": l["id"],
            "quizCount": quizzes,
            "questionCount": questions,
            "content": {"type": "doc", "content": doc},
        }


def build_topic(topic_dir):
    topic = json.loads((topic_dir / "topic.json").read_text(encoding="utf-8"))
    generator = {"html": html_lessons, "workbook-json": workbook_json_lessons}[topic["sourceFormat"]]
    out_dir = topic_dir / "lessons"
    out_dir.mkdir(exist_ok=True)
    written, index = set(), []
    for lesson_id, title, lesson in generator(topic, topic_dir):
        name = f"{lesson_id}-{slugify(re.sub(r'^\s*\d+\.\s*', '', title)) or 'lesson'}.json"
        (out_dir / name).write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.add(name)
        index.append({
            "id": lesson["id"], "course": lesson["course"], "unit": lesson["unit"],
            "lessonNumber": lesson["lessonNumber"], "title": lesson["title"], "level": lesson["level"],
            "file": f"lessons/{name}", "quizCount": lesson["quizCount"], "questionCount": lesson["questionCount"],
        })
    for stale in out_dir.glob("*.json"):
        if stale.name not in written:
            stale.unlink()
    index.sort(key=lambda e: e["lessonNumber"])
    (topic_dir / "index.json").write_text(
        json.dumps({**topic, "lessons": index}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(index)


def main():
    def is_workbook(path):
        return json.loads((path / "topic.json").read_text(encoding="utf-8")).get("sourceFormat") in ("html", "workbook-json")

    targets = [ROOT / a for a in sys.argv[1:]] or [p.parent for p in sorted(ROOT.glob("*/*/topic.json")) if is_workbook(p.parent)]
    try:
        for topic_dir in targets:
            print(f"{topic_dir.relative_to(ROOT)}: {build_topic(topic_dir)} lições geradas")
    except SourceError as err:
        sys.exit(f"ERRO: {err}")


if __name__ == "__main__":
    main()
