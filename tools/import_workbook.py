#!/usr/bin/env python3
"""Importa uma apostila exportada da plataforma para a estrutura do repositório.

Uso:
    python3 tools/import_workbook.py EXPORT.json --language pt --slug essentials \\
        --code essentials --description "..."

Dois formatos de exportação são reconhecidos:

  html            {id, title, level, coverURL, guidelines, lessons: [{docID, title, unit, content(HTML)}]}
                  -> source/manifest.json + source/<id>-<slug>.html + guidelines.md
  workbook-json   {title, version, description, lesson_timing_minutes, levels, lessons: [{lesson_number, id, student, teacher, ...}]}
                  -> source/<id>-<slug>.json (uma lição por arquivo)

Em ambos os casos grava <language>/<slug>/topic.json. O `token=` dos URLs do Firebase
Storage é removido (o repositório é público e os arquivos já têm leitura pública).
Depois rode `python3 tools/build_workbooks.py <language>/<slug>`.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from html_to_tiptap import strip_tokens  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NEWLINE_AFTER = re.compile(r"(</(?:p|h[1-6]|ul|ol|li|blockquote|table|tr|[a-z]+-component|file-snippet)>|<hr>|<hr/>)")


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def pretty_html(html):
    """Uma quebra de linha depois dos blocos, para o arquivo ficar legível no git."""
    return NEWLINE_AFTER.sub(r"\1\n", html).strip() + "\n"


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def import_html(export, args, topic_dir):
    source = topic_dir / "source"
    source.mkdir(parents=True, exist_ok=True)
    for old in list(source.glob("*.html")) + list(source.glob("manifest.json")):
        old.unlink()

    def sort_key(item):
        index, lesson = item
        number = re.match(r"\s*(\d+)", lesson["title"])
        # Dentro da unidade: numeradas na ordem do título, depois as sem número (revisões).
        return (lesson["unit"], int(number.group(1)) if number else 10 ** 6, index)

    ordered = [lesson for _, lesson in sorted(enumerate(export["lessons"]), key=sort_key)]
    manifest = []
    for number, lesson in enumerate(ordered, 1):
        lesson_id = f"{args.code}-{number:02d}"
        title_slug = slugify(re.sub(r"^\s*\d+\.\s*", "", lesson["title"])) or "lesson"
        name = f"{lesson_id}-{title_slug}.html"
        (source / name).write_text(pretty_html(strip_tokens(lesson["content"])), encoding="utf-8")
        manifest.append({
            "id": lesson_id,
            "file": name,
            "title": lesson["title"].strip(),
            "unit": lesson["unit"],
            "legacyId": lesson["docID"],
        })
    write_json(source / "manifest.json", manifest)

    guidelines = (export.get("guidelines") or "").strip()
    if guidelines:
        (topic_dir / "guidelines.md").write_text(strip_tokens(guidelines) + "\n", encoding="utf-8")

    topic = {
        "language": args.language,
        "mainTopic": export["title"],
        "slug": args.slug,
        "sourceFormat": "html",
        "description": args.description,
        "level": export["level"],
        "coverUrl": strip_tokens(export.get("coverURL") or ""),
        "legacyWorkbookId": export["id"],
        "structureNote": "Lições importadas da plataforma antiga: o HTML original fica em `source/` e o JSON Tiptap "
                         "em `lessons/` é gerado por `tools/build_workbooks.py`. Os componentes customizados antigos "
                         "(dica, professor, aluno, meta, revisão, exercício…) viram blockquotes, listas e quizzes.",
        "courses": [{"code": args.code, "name": export["title"], "lessons": len(manifest)}],
        "officialReferences": [],
    }
    if guidelines:
        topic["guidelines"] = "guidelines.md"
    write_json(topic_dir / "topic.json", topic)
    return len(manifest)


def import_workbook_json(export, args, topic_dir):
    source = topic_dir / "source"
    source.mkdir(parents=True, exist_ok=True)
    for old in source.glob("*.json"):
        old.unlink()
    lessons = sorted(export["lessons"], key=lambda l: l["lesson_number"])
    for lesson in lessons:
        name = f"{args.code}-{lesson['lesson_number']:02d}-{slugify(lesson['title'])}.json"
        write_json(source / name, lesson)
    timing = export["lesson_timing_minutes"]
    topic = {
        "language": args.language,
        "mainTopic": args.main_topic or export["title"],
        "slug": args.slug,
        "sourceFormat": "workbook-json",
        "description": args.description or export["description"],
        "durationMinutes": timing["total"],
        "format": "online, individual",
        "lessonPlan": " · ".join(
            f"{label} {timing[key]} min" for key, label in (
                ("lets_begin_and_explanation", "Let's begin and explanation"), ("practice_1", "Practice 1"),
                ("review", "Review"), ("practice_2", "Practice 2"), ("speaking_practice", "Speaking practice"),
                ("homework_explanation", "Homework explanation"))),
        "levels": export["levels"],
        "version": export["version"],
        "structureNote": "Cada lição tem material do aluno (`student`) e do professor (`teacher`: revisão espaçada, "
                         "gabaritos, scripts de listening e modelos de fala). O JSON original fica em `source/` e o "
                         "Tiptap em `lessons/` é gerado por `tools/build_workbooks.py`.",
        "courses": [{"code": args.code, "name": args.main_topic or export["title"], "lessons": len(lessons)}],
        "officialReferences": [],
    }
    write_json(topic_dir / "topic.json", topic)
    return len(lessons)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("export", type=Path)
    parser.add_argument("--language", required=True, help="idioma das explicações (pt, en)")
    parser.add_argument("--slug", required=True, help="pasta do tópico")
    parser.add_argument("--code", required=True, help="prefixo dos ids das lições")
    parser.add_argument("--description", default="")
    parser.add_argument("--main-topic", default="", help="nome do tópico (padrão: título da apostila)")
    args = parser.parse_args()

    export = json.loads(args.export.read_text(encoding="utf-8"))
    topic_dir = ROOT / args.language / args.slug
    topic_dir.mkdir(parents=True, exist_ok=True)
    if "docID" in (export.get("lessons") or [{}])[0]:
        count = import_html(export, args, topic_dir)
    elif "lesson_number" in (export.get("lessons") or [{}])[0]:
        count = import_workbook_json(export, args, topic_dir)
    else:
        sys.exit("ERRO: formato de exportação não reconhecido")
    print(f"{topic_dir.relative_to(ROOT)}: {count} lições importadas")


if __name__ == "__main__":
    main()
