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
| [`pt/essentials`](pt/essentials/README.md) | 27 | Apostila Essentials: gramática essencial do inglês com explicações em português |
| [`pt/first-steps`](pt/first-steps/README.md) | 50 | Apostila First Steps: primeiros passos no inglês, com práticas de escuta, leitura, escrita e conversação |
| [`pt/the-basics`](pt/the-basics/README.md) | 31 | Apostila The Basics: inglês básico com explicações em português, sessões de prática e revisões |
| [`pt/travelling`](pt/travelling/README.md) | 12 | Apostila Travelling: inglês para viagens (aeroporto, hotel, transporte, restaurante, saúde) |
| [`pt/deep-dive`](pt/deep-dive/README.md) | 49 | Apostila Deep Dive: gramática e uso do inglês em profundidade, de pronomes a phrasal verbs |
| [`pt/juridico`](pt/juridico/README.md) | 42 | Apostila Jurídico: inglês jurídico (terminologia, contratos, sentenças, estudos de caso) |
| [`en/brazilian-portuguese`](en/brazilian-portuguese/README.md) | 60 | Português brasileiro para falantes de inglês (A0 → B2), aulas de 45 minutos com material do professor |

Total: **551 lições**.

- As **280** primeiras (IELTS/TOEFL e os 6 cursos gerais) são escritas em Markdown: online, individuais, de 45 minutos, com foco em fala e vocabulário e homework para os 7 dias da semana.
- As **271** restantes são apostilas importadas da plataforma (`pt/essentials`, `pt/first-steps`, `pt/the-basics`, `pt/travelling`, `pt/deep-dive`, `pt/juridico`, `en/brazilian-portuguese`) e mantêm a estrutura própria de cada apostila.

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

## Apostilas importadas da plataforma

Tópicos com `sourceFormat` no `topic.json` vêm de apostilas exportadas da plataforma. O original fica em `source/` (HTML com `manifest.json`, ou um JSON por lição) e o JSON Tiptap de `lessons/` é gerado a partir dele:

```bash
# 1. exportação -> source/ + topic.json (formato html ou workbook-json, detectado sozinho)
python3 tools/import_workbook.py EXPORT.json --language pt --slug essentials --code essentials --description "..."
# 2. source/ -> lessons/*.json + index.json
python3 tools/build_workbooks.py
python3 tools/validate_lessons.py
python3 tools/build_readmes.py
```

- `language` é o idioma das explicações: `pt` para as apostilas de inglês para falantes de português (Essentials, First Steps, The Basics, Travelling, Deep Dive e Jurídico); `en` para o curso de Português Brasileiro, explicado em inglês.
- **HTML → Tiptap** (`tools/html_to_tiptap.py`): títulos, listas, task lists, tabelas, blocos de código, links, cores e alinhamento viram nós/marcas Tiptap. Os componentes customizados da plataforma antiga (dica, professor, aluno, meta semanal, revisão, tradução, imagem, listening, arquivo) não existem no editor atual e viram blockquotes, títulos, listas e links. Os `exercise-component` viram nós `quiz` com perguntas escritas.
- Os `token=` dos URLs do Firebase Storage antigo são removidos: o repositório é público e os arquivos têm leitura pública.
- Cada lição guarda o id original em `legacyId`.
- `tools/build_lessons.py` (Markdown) ignora esses tópicos, e `tools/build_workbooks.py` ignora os de Markdown.
