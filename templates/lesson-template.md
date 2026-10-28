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
