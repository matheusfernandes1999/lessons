# Lessons

Repositório de aulas, organizado sempre como:

```
<language>/<main_topic>/
  topic.json        metadados do tópico (cursos, referências)
  index.json        índice gerado de todas as lições
  source/*.md       lições editáveis (Markdown + blocos :::quiz)
  lessons/*.json    lições prontas para o banco (geradas)
```

- `language`: idioma do material (ex.: `pt` = explicações em português).
- `main_topic`: tópico principal (ex.: `ielts-and-toefl`).
- Cada lição tem título, nível, foco, tarefa verificável, habilidades e `content` (documento Tiptap/ProseMirror com nós `quiz` interativos).

## Tópicos

| Tópico | Lições | Descrição |
|---|---|---|
| [`pt/ielts-and-toefl`](pt/ielts-and-toefl/README.md) | 100 (50 TOEFL iBT + 50 IELTS Academic) | Preparação para TOEFL iBT (formato 2026) e IELTS Academic, aulas individuais online de 45 min |

## Template padrão

- [`templates/lesson-template.md`](templates/lesson-template.md) — estrutura pedagógica da aula de 45 min, técnicas e formato do arquivo-fonte.
- [`templates/lesson-template.json`](templates/lesson-template.json) — exemplo do JSON final.

## Gerar e validar os JSON

```bash
python3 tools/build_lessons.py      # source/*.md -> lessons/*.json + index.json
python3 tools/validate_lessons.py   # confere as regras do nó quiz e a estrutura das lições
```

Edite sempre o arquivo em `source/` e rode o build; não edite os JSON à mão.
