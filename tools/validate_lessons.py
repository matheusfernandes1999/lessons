#!/usr/bin/env python3
"""Valida os JSON gerados em */*/lessons/ contra as regras do nó Tiptap `quiz`.

Uso: python3 tools/validate_lessons.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSON_KEYS = ["id", "language", "mainTopic", "course", "unit", "lessonNumber", "title",
               "level", "durationMinutes", "focus", "verifiableTask", "skills", "content"]
# Lições importadas de apostilas em HTML não têm foco/tarefa/duração por lição.
HTML_LESSON_KEYS = ["id", "language", "mainTopic", "course", "unit", "lessonNumber", "title",
                    "level", "sourceFormat", "legacyId", "content"]
NODE_TYPES = {"doc", "paragraph", "heading", "text", "hardBreak", "bulletList", "orderedList", "listItem",
              "taskList", "taskItem", "blockquote", "codeBlock", "horizontalRule", "table", "tableRow", "tableCell",
              "tableHeader", "image", "quiz"}
MARK_TYPES = {"bold", "italic", "underline", "strike", "code", "link", "textStyle", "highlight"}
NEEDS_CONTENT = {"bulletList", "orderedList", "listItem", "taskList", "taskItem", "blockquote", "table",
                 "tableRow", "tableCell", "tableHeader", "heading"}
CATEGORIES = {"comprehension", "grammar", "vocabulary", "review"}


def check_quiz(node, where, errors):
    attrs = node.get("attrs", {})
    if set(attrs) != {"nodeId", "questions", "studentAnswers", "submitted"}:
        errors.append(f"{where}: attrs inesperados {sorted(attrs)}")
    if attrs.get("studentAnswers") != {} or attrs.get("submitted") is not False:
        errors.append(f"{where}: studentAnswers/submitted devem ser {{}}/false")
    questions = attrs.get("questions") or []
    if not questions:
        errors.append(f"{where}: quiz sem perguntas")
    ids = [q.get("id") for q in questions]
    if len(ids) != len(set(ids)):
        errors.append(f"{where}: ids de pergunta repetidos")
    for q in questions:
        qw = f"{where}/{q.get('id')}"
        if q.get("category") not in CATEGORIES:
            errors.append(f"{qw}: categoria inválida")
        if not q.get("questionText"):
            errors.append(f"{qw}: questionText vazio")
        if not isinstance(q.get("explanations"), dict) or not q["explanations"]:
            errors.append(f"{qw}: explanations ausente")
        if q.get("type") == "multiple-choice":
            opts = q.get("options") or []
            if not 2 <= len(opts) <= 4:
                errors.append(f"{qw}: precisa de 2 a 4 opções")
            if q.get("correctOptionId") not in {o["id"] for o in opts}:
                errors.append(f"{qw}: correctOptionId inválido")
            if "correctWrittenAnswer" in q:
                errors.append(f"{qw}: multiple-choice com correctWrittenAnswer")
        elif q.get("type") == "written":
            if not str(q.get("correctWrittenAnswer", "")).strip():
                errors.append(f"{qw}: correctWrittenAnswer vazio")
            if "options" in q:
                errors.append(f"{qw}: written com options")
        else:
            errors.append(f"{qw}: type inválido {q.get('type')}")


def check_node(node, where, errors):
    """Checagem leve de schema: tipos/marcas conhecidos, texto não vazio, conteúdo obrigatório."""
    kind = node.get("type")
    if kind not in NODE_TYPES:
        errors.append(f"{where}: tipo de nó desconhecido {kind}")
        return
    if kind == "text":
        if not node.get("text"):
            errors.append(f"{where}: nó de texto vazio")
        for mark in node.get("marks", []):
            if mark.get("type") not in MARK_TYPES:
                errors.append(f"{where}: marca desconhecida {mark.get('type')}")
            if mark.get("type") == "link" and not mark.get("attrs", {}).get("href"):
                errors.append(f"{where}: link sem href")
        return
    if kind == "image" and not node.get("attrs", {}).get("src"):
        errors.append(f"{where}: imagem sem src")
    if kind in NEEDS_CONTENT and not node.get("content"):
        errors.append(f"{where}: {kind} sem conteúdo")
    for child in node.get("content", []):
        check_node(child, where, errors)


def main():
    errors = []
    total_lessons = total_quizzes = total_questions = 0
    for path in sorted(ROOT.glob("*/*/lessons/*.json")):
        where = str(path.relative_to(ROOT))
        lesson = json.loads(path.read_text(encoding="utf-8"))
        total_lessons += 1
        source_format = lesson.get("sourceFormat")
        for key in (HTML_LESSON_KEYS if source_format == "html" else LESSON_KEYS):
            if lesson.get(key) in (None, "", []):
                errors.append(f"{where}: campo ausente {key}")
        if "token=" in path.read_text(encoding="utf-8"):
            errors.append(f"{where}: URL com token de download (repositório público)")
        doc = lesson.get("content", {})
        if doc.get("type") != "doc":
            errors.append(f"{where}: content.type deve ser 'doc'")
        check_node(doc, where, errors)
        node_ids = set()
        headings = []
        for i, node in enumerate(doc.get("content", [])):
            if node.get("type") == "heading":
                headings.append("".join(t.get("text", "") for t in node.get("content", [])))
            if node.get("type") == "quiz":
                total_quizzes += 1
                total_questions += len(node["attrs"]["questions"])
                nid = node["attrs"].get("nodeId")
                if nid in node_ids:
                    errors.append(f"{where}: nodeId repetido {nid}")
                node_ids.add(nid)
                check_quiz(node, f"{where}#{nid}", errors)
        if source_format != "html":
            objective = "Lesson objective" if source_format == "workbook-json" else "Objetivo"
            if not any(h.startswith(objective) for h in headings):
                errors.append(f"{where}: falta a seção '{objective}'")
            if not any("Homework" in h for h in headings):
                errors.append(f"{where}: falta a seção de Homework")
            if len(node_ids) < 2:
                errors.append(f"{where}: menos de 2 quizzes")
        if "undefined" in path.read_text(encoding="utf-8"):
            errors.append(f"{where}: contém 'undefined'")
    for e in errors:
        print("ERRO:", e)
    print(f"{total_lessons} lições · {total_quizzes} quizzes · {total_questions} perguntas · {len(errors)} erros")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
