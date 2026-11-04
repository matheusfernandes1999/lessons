#!/usr/bin/env python3
"""Converte o HTML das apostilas da plataforma (saída do editor Tiptap antigo) em
documento Tiptap/ProseMirror JSON, o mesmo formato do campo `content` das demais lições.

Nós gerados (todos existem no editor atual): paragraph, heading, bulletList, orderedList,
taskList/taskItem, blockquote, codeBlock, horizontalRule, hardBreak, table/tableRow/tableCell/
tableHeader, image e quiz. Marcas: bold, italic, underline, strike, code, link,
textStyle (cor) e highlight.

Os componentes customizados da plataforma antiga não existem no editor atual e viram
nós padrão:

    pre                    -> codeBlock (as caixas de dica das apostilas são blocos de código)
    tip-component          -> blockquote "💡 texto"
    teacher-component      -> blockquote "🧑‍🏫 Professor: texto"
    student-component      -> blockquote "🧑‍🎓 Aluno: texto"
    goal-component         -> heading 3 "🎯 título" + descrição + lista de dias
    review-component       -> heading 3 "🔁 título" + parágrafo
    image-text-component   -> image (+ legenda em itálico)
    translation-component  -> parágrafo "N. frase → ______"
    exercise-component     -> nó quiz com perguntas `written` (um quiz por grupo seguido)
    listening-component    -> parágrafo "🎧 Áudio de listening (ID …)"
    embed-component        -> parágrafo com link
    file-snippet           -> parágrafo com link do arquivo
"""

import re
from html.parser import HTMLParser

VOID = {"br", "hr", "img", "input", "col", "meta", "link", "source", "embed", "wbr"}
BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "hr", "table",
    "div", "pre", "tip-component", "teacher-component", "student-component", "goal-component",
    "review-component", "image-text-component", "translation-component", "exercise-component",
    "listening-component", "embed-component", "file-snippet",
}
MARK_TAGS = {
    "strong": "bold", "b": "bold", "em": "italic", "i": "italic", "u": "underline",
    "s": "strike", "del": "strike", "strike": "strike", "code": "code",
}
LINK_DEFAULTS = {"target": "_blank", "rel": "noopener noreferrer nofollow", "class": None}


# ------------------------------------------------------------------ URLs

def strip_tokens(text):
    """Remove `token=` das URLs do Firebase Storage (o bucket é de leitura pública)."""
    text = re.sub(r"(&amp;|&)token=[0-9A-Za-z-]+", "", text)
    return re.sub(r"\?token=[0-9A-Za-z-]+&(amp;)?", "?", text)


# ------------------------------------------------------------------ DOM

class Node:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = []


class _DomBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs})
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_html(html):
    builder = _DomBuilder()
    builder.feed(html)
    builder.close()
    return builder.root


def parse_style(value):
    out = {}
    for part in (value or "").split(";"):
        key, _, val = part.partition(":")
        if key.strip():
            out[key.strip().lower()] = val.strip()
    return out


# ------------------------------------------------------------------ inline

def text_node(text, marks):
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = [dict(m) for m in marks]
    return node


def merge_text(nodes):
    merged = []
    for node in nodes:
        if (merged and node["type"] == "text" and merged[-1]["type"] == "text"
                and merged[-1].get("marks") == node.get("marks")):
            merged[-1]["text"] += node["text"]
        else:
            merged.append(node)
    return merged


def inline(node, marks=()):
    """Nós inline (texto/hardBreak) de um elemento ou string."""
    if isinstance(node, str):
        return [text_node(node, marks)] if node else []
    tag = node.tag
    if tag == "br":
        return [{"type": "hardBreak"}]
    new = list(marks)
    if tag in MARK_TAGS:
        new.append({"type": MARK_TAGS[tag]})
    elif tag == "a" and node.attrs.get("href"):
        attrs = {"href": node.attrs["href"],
                 "target": node.attrs.get("target") or LINK_DEFAULTS["target"],
                 "rel": node.attrs.get("rel") or LINK_DEFAULTS["rel"],
                 "class": None}
        new.append({"type": "link", "attrs": attrs})
    elif tag == "span":
        style = parse_style(node.attrs.get("style"))
        if "color" in style:
            new.append({"type": "textStyle", "attrs": {"color": style["color"]}})
        if "background-color" in style:
            new.append({"type": "highlight", "attrs": {"color": style["background-color"]}})
    elif tag in ("label", "input"):
        return []
    out = []
    for child in node.children:
        out.extend(inline(child, new))
    return out


# ------------------------------------------------------------------ blocks

def paragraph(nodes, align=None):
    nodes = merge_text(nodes)
    node = {"type": "paragraph"}
    if align:
        node["attrs"] = {"textAlign": align}
    if nodes:
        node["content"] = nodes
    return node


def plain_paragraph(*parts):
    """Parágrafo a partir de (texto, [marcas]) ou strings."""
    nodes = []
    for part in parts:
        text, marks = part if isinstance(part, tuple) else (part, ())
        if text:
            nodes.append(text_node(text, marks))
    return paragraph(nodes)


def alignment(node):
    value = parse_style(node.attrs.get("style")).get("text-align")
    return value if value in ("center", "right", "justify") else None


def plain_text(node):
    """Texto puro de um elemento (para blocos de código)."""
    if isinstance(node, str):
        return node
    return "\n" if node.tag == "br" else "".join(plain_text(c) for c in node.children)


def has_block_child(node):
    return any(not isinstance(c, str) and c.tag in BLOCK_TAGS for c in node.children)


def blocks(children, ctx):
    out, pending = [], []

    def flush():
        nonlocal pending
        merged = merge_text(pending)
        if any(n["type"] != "text" or n["text"].strip() for n in merged):
            out.append(paragraph(merged))
        pending = []

    i = 0
    while i < len(children):
        child = children[i]
        if isinstance(child, str):
            pending.extend(inline(child))
        elif child.tag == "exercise-component":
            flush()
            group = []
            while i < len(children) and (
                    (isinstance(children[i], str) and not children[i].strip())
                    or (not isinstance(children[i], str) and children[i].tag == "exercise-component")):
                if not isinstance(children[i], str):
                    group.append(children[i])
                i += 1
            out.append(exercise_quiz(group, ctx))
            continue
        elif child.tag in BLOCK_TAGS:
            flush()
            out.extend(block(child, ctx))
        else:
            pending.extend(inline(child))
        i += 1
    flush()
    return out


def list_items(node, ctx, task=False):
    items = []
    for child in node.children:
        if isinstance(child, str) or child.tag != "li":
            continue
        if task:
            body = [c for c in child.children if not isinstance(c, str) and c.tag == "div"]
            content = blocks(body[0].children, ctx) if body else blocks(
                [c for c in child.children if isinstance(c, str) or c.tag not in ("label", "input")], ctx)
            items.append({"type": "taskItem", "attrs": {"checked": child.attrs.get("data-checked") == "true"},
                          "content": content or [{"type": "paragraph"}]})
        else:
            content = blocks(child.children, ctx)
            items.append({"type": "listItem", "content": content or [{"type": "paragraph"}]})
    return items


def table(node, ctx):
    rows = []

    def collect(parent):
        for child in parent.children:
            if isinstance(child, str):
                continue
            if child.tag == "tr":
                cells = []
                for cell in child.children:
                    if isinstance(cell, str) or cell.tag not in ("td", "th"):
                        continue
                    colwidth = cell.attrs.get("colwidth")
                    attrs = {
                        "colspan": int(cell.attrs.get("colspan") or 1),
                        "rowspan": int(cell.attrs.get("rowspan") or 1),
                        "colwidth": [int(w) for w in colwidth.split(",") if w.strip().isdigit()] if colwidth else None,
                    }
                    cells.append({
                        "type": "tableHeader" if cell.tag == "th" else "tableCell",
                        "attrs": attrs,
                        "content": blocks(cell.children, ctx) or [{"type": "paragraph"}],
                    })
                if cells:  # <tr></tr> vazio no HTML original não aparece na tela
                    rows.append({"type": "tableRow", "content": cells})
            elif child.tag in ("tbody", "thead", "tfoot"):
                collect(child)

    collect(node)
    return {"type": "table", "content": rows} if rows else None


def block(node, ctx):
    tag = node.tag
    if tag == "p":
        if has_block_child(node):
            return blocks(node.children, ctx)
        nodes = []
        for child in node.children:
            nodes.extend(inline(child))
        return [paragraph(nodes, alignment(node))]
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        nodes = []
        for child in node.children:
            nodes.extend(inline(child))
        nodes = merge_text(nodes)
        if not any(n["type"] != "text" or n["text"].strip() for n in nodes):
            return []  # título vazio no HTML original: não aparece na tela
        attrs = {"level": int(tag[1])}
        if alignment(node):
            attrs["textAlign"] = alignment(node)
        return [{"type": "heading", "attrs": attrs, "content": nodes}]
    if tag == "ul":
        if node.attrs.get("data-type") == "taskList":
            return [{"type": "taskList", "content": list_items(node, ctx, task=True)}]
        return [{"type": "bulletList", "content": list_items(node, ctx)}]
    if tag == "ol":
        start = int(node.attrs["start"]) if str(node.attrs.get("start", "")).isdigit() else 1
        return [{"type": "orderedList", "attrs": {"start": start}, "content": list_items(node, ctx)}]
    if tag == "li":
        return blocks(node.children, ctx)
    if tag == "blockquote":
        return [{"type": "blockquote", "content": blocks(node.children, ctx) or [{"type": "paragraph"}]}]
    if tag == "hr":
        return [{"type": "horizontalRule"}]
    if tag == "pre":
        code = "".join(plain_text(c) for c in node.children)
        node_out = {"type": "codeBlock", "attrs": {"language": None}}
        if code.strip():
            node_out["content"] = [{"type": "text", "text": code}]
        return [node_out]
    if tag == "table":
        converted = table(node, ctx)
        return [converted] if converted else []
    if tag in COMPONENTS:
        return COMPONENTS[tag](node, ctx)
    return blocks(node.children, ctx)  # div, pre e afins: só desembrulha


# ------------------------------------------------------------------ componentes antigos

def _clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def c_tip(node, ctx):
    return [{"type": "blockquote", "content": [plain_paragraph("💡 " + _clean(node.attrs.get("text")))]}]


def c_teacher(node, ctx):
    return [{"type": "blockquote", "content": [
        plain_paragraph(("🧑‍🏫 Professor: ", [{"type": "bold"}]), _clean(node.attrs.get("text")))]}]


def c_student(node, ctx):
    return [{"type": "blockquote", "content": [
        plain_paragraph(("🧑‍🎓 Aluno: ", [{"type": "bold"}]), _clean(node.attrs.get("text")))]}]


def c_goal(node, ctx):
    out = [{"type": "heading", "attrs": {"level": 3},
            "content": [text_node("🎯 " + _clean(node.attrs.get("title")), ())]}]
    if _clean(node.attrs.get("description")):
        out.append(plain_paragraph(_clean(node.attrs["description"])))
    days = [d.strip() for d in (node.attrs.get("schedule") or "").split("\n") if d.strip()]
    if days:
        out.append({"type": "bulletList", "content": [
            {"type": "listItem", "content": [plain_paragraph(d)]} for d in days]})
    return out


def c_review(node, ctx):
    out = [{"type": "heading", "attrs": {"level": 3},
            "content": [text_node("🔁 " + _clean(node.attrs.get("title")), ())]}]
    if _clean(node.attrs.get("content")):
        out.append(plain_paragraph(_clean(node.attrs["content"])))
    return out


def c_image(node, ctx):
    url = node.attrs.get("imageurl")
    if not url:
        return []
    out = [{"type": "image", "attrs": {"src": url, "alt": _clean(node.attrs.get("text")) or None, "title": None}}]
    if _clean(node.attrs.get("text")):
        out.append(plain_paragraph((_clean(node.attrs["text"]), [{"type": "italic"}])))
    return out


def c_translation(node, ctx):
    number = _clean(node.attrs.get("sentencenumber"))
    prefix = f"{number}. " if number else ""
    nodes = []
    if prefix:
        nodes.append(text_node(prefix, [{"type": "bold"}]))
    nodes += [
        text_node(_clean(node.attrs.get("originalsentence")), ()),
        {"type": "hardBreak"},
        text_node("→ ______", ()),
    ]
    return [paragraph(nodes)]


def c_listening(node, ctx):
    return [plain_paragraph((f"🎧 Áudio de listening (ID {node.attrs.get('audioid', '')})", [{"type": "italic"}]))]


def _link(text, href):
    return text_node(text, [{"type": "link", "attrs": {"href": href, **LINK_DEFAULTS}}])


def c_embed(node, ctx):
    url = node.attrs.get("url")
    return [paragraph([text_node("🔗 ", ()), _link(url, url)])] if url else []


def c_file(node, ctx):
    url = node.attrs.get("fileurl")
    if not url:
        return []
    name, desc = _clean(node.attrs.get("filename")), _clean(node.attrs.get("description"))
    nodes = [text_node("📎 ", ()), _link(desc or name or url, url)]
    if desc and name:
        nodes.append(text_node(f" ({name})", ()))
    return [paragraph(nodes)]


COMPONENTS = {
    "tip-component": c_tip, "teacher-component": c_teacher, "student-component": c_student,
    "goal-component": c_goal, "review-component": c_review, "image-text-component": c_image,
    "translation-component": c_translation, "listening-component": c_listening,
    "embed-component": c_embed, "file-snippet": c_file,
}


def exercise_quiz(group, ctx):
    """Grupo seguido de exercise-component -> um nó quiz com perguntas `written`."""
    ctx["quiz_count"] = ctx.get("quiz_count", 0) + 1
    short = f"ex{ctx['quiz_count']}"
    questions = []
    for n, node in enumerate(group, 1):
        sentence = _clean(node.attrs.get("sentence")).replace("{{gap}}", "______")
        answer = _clean(node.attrs.get("answer"))
        questions.append({
            "id": f"{short}-gap-{n}",
            "category": "vocabulary",
            "questionText": sentence,
            "type": "written",
            "correctWrittenAnswer": answer,
            "explanations": {"general": answer},
        })
    return {"type": "quiz", "attrs": {
        "nodeId": f"quiz_{ctx['lesson_key']}_{short}",
        "questions": questions, "studentAnswers": {}, "submitted": False}}


# ------------------------------------------------------------------ API

def html_to_doc(html, lesson_key):
    """HTML de uma lição -> {"type": "doc", "content": [...]}."""
    ctx = {"lesson_key": lesson_key}
    content = blocks(parse_html(html).children, ctx)
    return {"type": "doc", "content": content}
