#!/usr/bin/env python3
"""Converte as lições escritas em Markdown (pasta source/) em JSON prontos para o banco.

Uso:
    python3 tools/build_lessons.py                # todos os tópicos
    python3 tools/build_lessons.py pt/ielts-and-toefl

Estrutura esperada:
    <language>/<main_topic>/topic.json            metadados do tópico
    <language>/<main_topic>/source/*.md           lições (front matter + Markdown + blocos :::quiz)
    <language>/<main_topic>/lessons/*.json        saída gerada (não editar à mão)

O formato da fonte está documentado em templates/lesson-source-format.md.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- inline marks

def inline(text):
    """Texto com **negrito** e *itálico* (podem ser aninhados) -> nós de texto Tiptap."""
    if text.count("**") % 2 or (text.count("*") - 2 * text.count("**")) % 2:
        raise SourceError(f"marcação * sem par: {text}")
    nodes = []
    bold = italic = False
    buf = ""
    i = 0

    def flush():
        if buf:
            marks = ([{"type": "bold"}] if bold else []) + ([{"type": "italic"}] if italic else [])
            node = {"type": "text", "text": buf}
            if marks:
                node["marks"] = marks
            nodes.append(node)

    while i < len(text):
        if text.startswith("**", i):
            flush()
            buf = ""
            bold = not bold
            i += 2
        elif text[i] == "*":
            flush()
            buf = ""
            italic = not italic
            i += 1
        else:
            buf += text[i]
            i += 1
    flush()
    return nodes


def paragraph(text):
    content = inline(text)
    return {"type": "paragraph", "content": content} if content else {"type": "paragraph"}


def plain(text):
    return text.replace("**", "").replace("*", "")


# ---------------------------------------------------------------- quiz blocks

OPTION_RE = re.compile(r"^(\*)?([A-D])\)\s*(.+)$")
QUESTION_RE = re.compile(r"^\?\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(.+)$")
CATEGORIES = {"comprehension", "grammar", "vocabulary", "review"}
SHORT_TYPES = {"mc": "mc", "w": "w", "gap": "w", "tf": "tf", "tfng": "tfng", "ynng": "ynng"}
FIXED_OPTIONS = {
    "tf": [("A", "True"), ("B", "False")],
    "tfng": [("A", "True"), ("B", "False"), ("C", "Not Given")],
    "ynng": [("A", "Yes"), ("B", "No"), ("C", "Not Given")],
}
FIXED_ANSWERS = {
    "t": "A", "true": "A", "f": "B", "false": "B",
    "y": "A", "yes": "A", "n": "B", "no": "B", "ng": "C", "not given": "C",
}


class SourceError(Exception):
    pass


def parse_quiz(lines, node_id, where):
    questions = []
    current = None
    counters = {}

    def finish():
        if current is None:
            return
        questions.append(build_question(current, where))

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = QUESTION_RE.match(line)
        if m:
            finish()
            kind = SHORT_TYPES.get(m.group(1).lower())
            if kind is None:
                raise SourceError(f"{where}: tipo de pergunta desconhecido '{m.group(1)}'")
            category = m.group(2).lower()
            if category not in CATEGORIES:
                raise SourceError(f"{where}: categoria inválida '{category}'")
            prefix = "gap" if kind == "w" else ("tf" if kind in FIXED_OPTIONS else "mc")
            counters[prefix] = counters.get(prefix, 0) + 1
            short = node_id.rsplit("_", 1)[-1]
            current = {
                "id": f"{short}-{prefix}-{counters[prefix]}",
                "kind": kind,
                "category": category,
                "questionText": m.group(3).strip(),
                "options": [],
                "correct": None,
                "answer": None,
                "explanations": {},
            }
            continue
        if current is None:
            raise SourceError(f"{where}: linha fora de pergunta: {line}")
        if line.startswith("= "):
            current["explanations"]["general"] = line[2:].strip()
            continue
        if line.startswith("> "):
            current["answer"] = line[2:].strip()
            continue
        m = OPTION_RE.match(line)
        if m and current["kind"] == "mc":
            text, _, expl = m.group(3).partition("||")
            current["options"].append({"id": m.group(2), "text": text.strip()})
            if expl.strip():
                current["explanations"][m.group(2)] = expl.strip()
            if m.group(1):
                current["correct"] = m.group(2)
            continue
        raise SourceError(f"{where}: linha não reconhecida no quiz: {line}")
    finish()
    if not 1 <= len(questions):
        raise SourceError(f"{where}: quiz vazio")
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        raise SourceError(f"{where}: ids repetidos")
    return {
        "type": "quiz",
        "attrs": {
            "nodeId": node_id,
            "questions": questions,
            "studentAnswers": {},
            "submitted": False,
        },
    }


def build_question(q, where):
    kind = q["kind"]
    out = {"id": q["id"], "category": q["category"], "questionText": q["questionText"]}
    expl = dict(q["explanations"])
    if kind == "w":
        if not q["answer"]:
            raise SourceError(f"{where}: pergunta escrita sem resposta: {q['questionText']}")
        out["type"] = "written"
        out["correctWrittenAnswer"] = q["answer"]
        if "general" not in expl:
            expl["general"] = q["answer"]
        out["explanations"] = {"general": expl["general"]}
        return out
    out["type"] = "multiple-choice"
    if kind in FIXED_OPTIONS:
        options = [{"id": i, "text": t} for i, t in FIXED_OPTIONS[kind]]
        correct = FIXED_ANSWERS.get((q["answer"] or "").lower())
        if correct is None or correct not in {o["id"] for o in options}:
            raise SourceError(f"{where}: resposta inválida '{q['answer']}' em {q['questionText']}")
    else:
        options = q["options"]
        correct = q["correct"]
        if not 2 <= len(options) <= 4:
            raise SourceError(f"{where}: precisa de 2 a 4 opções: {q['questionText']}")
        if correct is None:
            raise SourceError(f"{where}: sem opção correta (*): {q['questionText']}")
    out["options"] = options
    out["correctOptionId"] = correct
    if "general" not in expl:
        text = next(o["text"] for o in options if o["id"] == correct)
        expl["general"] = f"Correct answer: {text}"
    out["explanations"] = expl
    return out


# ---------------------------------------------------------------- markdown body

def parse_body(text, lesson_key, where):
    lines = text.split("\n")
    doc = []
    i = 0
    node_ids = set()
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith(":::quiz"):
            name = stripped[len(":::quiz"):].strip()
            if not name:
                raise SourceError(f"{where}: bloco :::quiz sem nome (linha {i + 1})")
            block = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                block.append(lines[i])
                i += 1
            if i >= len(lines):
                raise SourceError(f"{where}: bloco :::quiz {name} não foi fechado")
            node_id = f"quiz_{lesson_key}_{name}"
            if node_id in node_ids:
                raise SourceError(f"{where}: nodeId repetido {node_id}")
            node_ids.add(node_id)
            doc.append(parse_quiz(block, node_id, f"{where} [{name}]"))
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if m:
            doc.append({
                "type": "heading",
                "attrs": {"level": len(m.group(1))},
                "content": inline(m.group(2).strip()),
            })
            i += 1
            continue
        if stripped == "---":
            doc.append({"type": "horizontalRule"})
            i += 1
            continue
        if stripped.startswith(">"):
            paras = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                content = lines[i].strip()[1:].strip()
                if content:
                    paras.append(paragraph(content))
                i += 1
            doc.append({"type": "blockquote", "content": paras or [{"type": "paragraph"}]})
            continue
        if re.match(r"^[-•]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-•]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-•]\s+", "", lines[i].strip()))
                i += 1
            doc.append({
                "type": "bulletList",
                "content": [{"type": "listItem", "content": [paragraph(t)]} for t in items],
            })
            continue
        if re.match(r"^\d+\.\s+", stripped):
            start = int(re.match(r"^(\d+)\.", stripped).group(1))
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            doc.append({
                "type": "orderedList",
                "attrs": {"start": start},
                "content": [{"type": "listItem", "content": [paragraph(t)]} for t in items],
            })
            continue
        doc.append(paragraph(stripped))
        i += 1
    return doc


# ---------------------------------------------------------------- lesson files

def parse_front_matter(text, where):
    if not text.startswith("---\n"):
        raise SourceError(f"{where}: arquivo precisa começar com front matter (---)")
    end = text.index("\n---\n", 4)
    meta = {}
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[end + 5:]


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def text_of(node):
    if node.get("type") == "text":
        return node["text"]
    if node.get("type") == "quiz":
        return "\n".join(q["questionText"] for q in node["attrs"]["questions"])
    return "".join(text_of(c) for c in node.get("content", []))


REQUIRED = ["course", "courseCode", "number", "title", "level", "unit", "focus", "task", "skills"]


def build_lesson(path, topic):
    where = str(path.relative_to(ROOT))
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"), where)
    for key in REQUIRED:
        if not meta.get(key):
            raise SourceError(f"{where}: campo obrigatório ausente no front matter: {key}")
    number = int(meta["number"])
    code = meta["courseCode"]
    lesson_key = f"{code}{number:02d}"
    content = parse_body(body, lesson_key, where)
    for node in content:
        if node["type"] != "quiz" and "*" in text_of(node):
            raise SourceError(f"{where}: marcação * sem par: {text_of(node)[:80]}")
    quizzes = [n for n in content if n["type"] == "quiz"]
    lesson = {
        "id": f"{code}-{number:02d}",
        "language": topic["language"],
        "mainTopic": topic["mainTopic"],
        "course": meta["course"],
        "unit": meta["unit"],
        "lessonNumber": number,
        "title": meta["title"],
        "level": meta["level"],
        "durationMinutes": topic.get("durationMinutes", 45),
        "format": topic.get("format", "online, individual"),
        "focus": meta["focus"],
        "verifiableTask": meta["task"],
        "skills": [s.strip() for s in meta["skills"].split(",") if s.strip()],
        "quizCount": len(quizzes),
        "questionCount": sum(len(q["attrs"]["questions"]) for q in quizzes),
        "content": {"type": "doc", "content": content},
    }
    name = f"{code}-{number:02d}-{slugify(meta['title'])}.json"
    return name, lesson


def build_topic(topic_dir):
    topic = json.loads((topic_dir / "topic.json").read_text(encoding="utf-8"))
    out_dir = topic_dir / "lessons"
    out_dir.mkdir(exist_ok=True)
    written = set()
    index = []
    for path in sorted((topic_dir / "source").glob("*.md")):
        name, lesson = build_lesson(path, topic)
        (out_dir / name).write_text(
            json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        written.add(name)
        index.append({
            "id": lesson["id"],
            "course": lesson["course"],
            "unit": lesson["unit"],
            "lessonNumber": lesson["lessonNumber"],
            "title": lesson["title"],
            "level": lesson["level"],
            "file": f"lessons/{name}",
            "quizCount": lesson["quizCount"],
            "questionCount": lesson["questionCount"],
        })
    for stale in out_dir.glob("*.json"):
        if stale.name not in written:
            stale.unlink()
    index.sort(key=lambda e: (e["course"], e["lessonNumber"]))
    (topic_dir / "index.json").write_text(
        json.dumps({**topic, "lessons": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(index)


def main():
    targets = [ROOT / a for a in sys.argv[1:]] or sorted(p.parent for p in ROOT.glob("*/*/topic.json"))
    try:
        for topic_dir in targets:
            count = build_topic(topic_dir)
            print(f"{topic_dir.relative_to(ROOT)}: {count} lições geradas")
    except SourceError as err:
        sys.exit(f"ERRO: {err}")


if __name__ == "__main__":
    main()
