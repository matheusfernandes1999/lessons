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
| [`pt/ielts-and-toefl`](pt/ielts-and-toefl/README.md) | 100 (50 TOEFL iBT + 50 IELTS Academic) | Preparação para TOEFL iBT (formato 2026) e IELTS Academic |
| [`pt/american-english-and-culture`](pt/american-english-and-culture/README.md) | 30 | Inglês americano no dia a dia, cultura e tom (grafia US) |
| [`pt/british-english-and-culture`](pt/british-english-and-culture/README.md) | 30 | Inglês britânico, polidez e vida no Reino Unido (grafia UK) |
| [`pt/pronunciation-and-accent-training`](pt/pronunciation-and-accent-training/README.md) | 30 | Sons, tônica, fala conectada, entonação e sotaques US/UK |
| [`pt/professional-writing`](pt/professional-writing/README.md) | 30 | E-mails, relatórios, propostas, CV e revisão, sempre com parte oral (grafia UK) |
| [`pt/idioms-and-natural-expressions`](pt/idioms-and-natural-expressions/README.md) | 30 | Expressões idiomáticas e naturais, registro e variantes US/UK |
| [`pt/phrasal-verbs-in-context`](pt/phrasal-verbs-in-context/README.md) | 30 | Phrasal verbs por tema, verbos com vários sentidos e formalidade (grafia US) |

Total: **280 lições**, todas online, individuais, de 45 minutos, com foco em fala e vocabulário e homework para os 7 dias da semana.

## Template padrão

- [`templates/lesson-template.md`](templates/lesson-template.md) — estrutura pedagógica da aula de 45 min (variante de provas e variante dos cursos gerais), técnicas e formato do arquivo-fonte.
- [`templates/lesson-template.json`](templates/lesson-template.json) — exemplo do JSON final.

## Gerar e validar os JSON

```bash
python3 tools/build_lessons.py      # source/*.md -> lessons/*.json + index.json
python3 tools/validate_lessons.py   # confere as regras do nó quiz e a estrutura das lições
python3 tools/build_readmes.py      # atualiza os README dos tópicos (exceto os escritos à mão)
```

Edite sempre o arquivo em `source/` e rode o build; não edite os JSON à mão.
