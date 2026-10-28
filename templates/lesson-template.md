# Template padrão de lição (45 min, online, individual)

Este é o modelo usado em todas as lições do repositório. A lição é colada inteira em um documento compartilhado e **o professor edita junto com o aluno** durante a aula (acrescentando exemplos, corrigindo frases, anotando dúvidas). Por isso o material traz espaços em branco (`______`) e listas abertas para completar.

Prioridade em toda aula: **o aluno fala muito e aprende vocabulário usando-o**. Explicações são curtas e objetivas; o resto é exemplo, mini texto e mini exercício.

## Estrutura da aula

| Bloco | Tempo | O que acontece |
|---|---|---|
| Objetivo da aula | — | Foco, o que o aluno consegue fazer ao final e a tarefa verificável. |
| 1. Warm-up | 5 min | Perguntas para o aluno falar, frases úteis, "troque e fale", revisão da aula anterior. |
| 2. Vocabulário-chave | 4 min | 10–14 palavras/chunks com tradução e exemplo + bloco de pronúncia (pares e grupos de palavras parecidas) + quiz `vocab`. |
| 3. Explicação e modelo | 4 min | Explicação simples em português + texto/fala modelo para ler, repetir e falar junto. |
| 4. Prática guiada | 10 min | Exercícios de substituição oral, mini textos, mini exercícios + quiz `practice`. |
| 5. Tarefa cronometrada | 15 min | Tarefa no formato da prova, com cronômetro e espaço para registrar acertos/tempo. |
| 6. Feedback | 3 min | Checklist de critérios observáveis + 1 ponto forte e 1 ajuste. |
| 7. Homework da semana | 4 min | 7 dias de estudo (15–20 min/dia) + quiz `homework`. |
| Gabarito do professor | — | Respostas dos exercícios abertos (fica no fim para não atrapalhar o aluno). |

## Variante dos cursos gerais (cultura, pronúncia, escrita, idioms, phrasal verbs)

Os cursos fora de provas (American/British English and Culture, Pronunciation, Professional Writing, Idioms, Phrasal Verbs) usam a mesma ideia, com outro tempo e homework só com tarefas diárias:

| Bloco | Tempo | O que acontece |
|---|---|---|
| Objetivo da aula | — | Foco, o que o aluno consegue fazer ao final, tarefa verificável e notas (grafia, variantes, cuidados). |
| 1. Revisão e aquecimento | 5 min | Revisão rápida da aula anterior + 2–3 perguntas para o aluno falar. |
| 2. Apresentação e exemplos | 10 min | Vocabulário/expressões em grupos, exemplos, mini texto + bloco *Pronúncia: ouça, compare e repita* com frase para repetir 3 vezes + quiz `vocab`. |
| 3. Prática guiada | 10 min | Classificar, completar, “troque e fale”, ouvir e identificar + quiz `practice`. |
| 4. Tarefa comunicativa | 15 min | Simulação em cenas ou etapas com personagens e lugares fictícios; o professor anota critérios. |
| 5. Feedback | 5 min | Checklist `- [ ]` + ajuste. |
| Homework da semana (7 dias) | — | Uma tarefa curta por dia (10–20 min): **Dia 1 … Dia 6** + **Dia 7 — Revisão** com o quiz `homework`. Sem produto final único. |
| Gabarito do professor | — | Opcional: respostas dos exercícios abertos e textos-modelo. |

Cuidados de conteúdo nesses cursos:
- cenários e personagens **fictícios** — o aluno não precisa revelar dados pessoais;
- linguagem cautelosa sobre culturas (*many people, it varies*), sem generalizações sobre “todos os americanos/britânicos”;
- nada de conselho médico (aulas de saúde tratam só da parte administrativa ou de linguagem do dia a dia);
- grafia definida por curso: americana (American English, Phrasal Verbs), britânica (British English, Professional Writing) ou as duas com indicação (Pronunciation, Idioms);
- áudio de referência: botões **US** e **UK** do Cambridge Dictionary; trechos para o professor ler vêm marcados com 🎧.

## Técnicas usadas (sem nome técnico no material)

- **Ouça, compare e repita** (pares/grupos mínimos): grupos como *ship / sheep*, *think / sink / pink*; o professor fala uma palavra e o aluno identifica qual foi.
- **Troque e fale** (substituição): frase base + palavras para trocar; o aluno fala a frase inteira sem olhar.
- **Fale junto / sombra** (shadowing): o professor lê o modelo e o aluno fala ao mesmo tempo, no mesmo ritmo.
- **Aumente a frase** (back-chaining): repetir uma frase longa começando pelo fim.
- **Gravação**: no homework o aluno grava e compara com o modelo.

## Formato do arquivo-fonte (`source/*.md`)

```markdown
---
course: TOEFL iBT (2026)
courseCode: toefl
number: 1
title: Orientation and Exam Diagnostic
level: A2–B1
unit: Foundations and Diagnostic
focus: ...
task: ...
skills: speaking, vocabulary, listening
---

## Objetivo da aula
Parágrafo com **negrito** e *itálico*.
- item de lista
1. item numerado
> texto modelo (citação)
---            (linha horizontal)

:::quiz vocab
? mc|vocabulary|Pergunta de múltipla escolha
A) opção || explicação desta opção
*B) opção correta (marcada com *) || explicação
= explicação geral (opcional)
? w|grammar|Lacuna ______ (dica)
> resposta única
= frase completa
? tf|comprehension|Afirmação verdadeira ou falsa
> T
? tfng|comprehension|Afirmação (True / False / Not Given)
> NG
? ynng|comprehension|Afirmação (Yes / No / Not Given)
> Y
:::
```

- Categorias: `comprehension`, `grammar`, `vocabulary`, `review`.
- Cada linha de texto vira um parágrafo. Linhas seguidas com `-` viram uma lista.
- Cada bloco `:::quiz <nome>` vira um nó Tiptap `quiz` com `nodeId = quiz_<curso><nº>_<nome>`.

Gere os JSON com:

```bash
python3 tools/build_lessons.py
```

O script valida as regras do nó `quiz` (tipos, opções, resposta correta, ids únicos, `studentAnswers = {}`, `submitted = false`).

## Formato do JSON gerado

Veja `templates/lesson-template.json`. Campos principais: `id`, `language`, `mainTopic`, `course`, `unit`, `lessonNumber`, `title`, `level`, `durationMinutes`, `focus`, `verifiableTask`, `skills`, `quizCount`, `questionCount` e `content` (documento Tiptap/ProseMirror com os nós `quiz` como filhos diretos de `doc`).
