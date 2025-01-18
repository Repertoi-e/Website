from typing import Any, Callable
import sys

from enum import Enum

from datetime import date

import re
import os
import os.path

import shutil

from collections import OrderedDict

line_number: int = 0
version: int = 0
lines: list[str] = []


def report(msg: str, subtract_one_from_line_number: bool = False):
    print(f"[{line_number + 1 - (1 if subtract_one_from_line_number else 0)}] {msg}")


def eat_next_line(code: bool = False) -> tuple[str, bool]:
    """
    If code is false: skips empty lines and 
    strips resulting line from white space
    """
    global lines, line_number

    while line_number != len(lines):
        l = lines[line_number]
        line_number += 1

        if not code:
            l = l.rstrip()
            if len(l) == 0:  # Ignore regular empty lines
                continue
            if l.startswith("//"):  # Ignore comments
                continue
        return l, True
    return "", False


def return_line():
    """
    Use x to override with rest of the line if something 
    has been parsed, i.e. "return a "partial" line".
    """
    global line_number
    if line_number == 0:
        print("Internal error: returning first line...")
        return
    line_number -= 1


def expect_eat(l: str, str: str) -> tuple[str, bool]:
    if not l.startswith(str):
        return l, False
    if len(l) == len(str):
        return "", True
    return l[len(str):], True


def try_parse_version() -> bool:
    global version

    l, success = eat_next_line()
    if not success:
        return False

    rest, status = expect_eat(l, "@v")
    if not status:
        report(
            f'Unknown version on first line: "{l}". Use something like: @v1, @v2, etc.')
        return False

    version = int(rest)
    print(f"Parsed version number: {version}")
    return True


class Language(Enum):
    BULGARIAN = "bulgarian"
    ENGLISH = "english"


languages_dict: dict[str, Language] = {
    "en": Language.ENGLISH,
    "english": Language.ENGLISH,
    "bg": Language.BULGARIAN,
    "bulgarian": Language.BULGARIAN
}


class MessageSender(Enum):
    NOBODY = "NOBODY",
    SOTI = "SOTI",
    BEBKA = "BEBKA"


meta: dict[str, Any] = dict()


def get_localized_date_str(d: date) -> str:
    return d.strftime("%d.%m.%Y" if meta["lang"] == Language.ENGLISH else "%d.%m.%Y г.")


def get_localized_last_edit_str(d_str: str) -> str:
    return f"Last edited {d_str}" if meta["lang"] == Language.ENGLISH else f"Последна редакция {d_str}"


def get_localized_author_me_str() -> str:
    return "by Dimitar Sotirov" if meta["lang"] == Language.ENGLISH else "- Димитър Сотиров"


def get_localized_html_lang_meta_str() -> str:
    return '<html lang="en-GB">' if meta["lang"] == Language.ENGLISH else '<html lang="bg">'


class HTMLGen():
    src: list[str] = []

    current_message_sender: MessageSender = MessageSender.NOBODY

    raw: bool = False

    def set_message_sender(self, message_sender: MessageSender):
        if self.current_message_sender == message_sender:
            report(f"Already doing messages for {message_sender}!")
            return

        if self.current_message_sender == MessageSender.NOBODY:
            # Begin new section
            self.src.append('<div class="message_section">')
        else:
            self.src.append('</div></div>')

        if message_sender == MessageSender.SOTI:
            self.src.append(
                '<div class="message_soti_div"><div class="message_soti_container">')
        elif message_sender == MessageSender.BEBKA:
            self.src.append(
                '<div class="message_bebka_div"><div class="message_bebka_container">')
        elif message_sender == MessageSender.NOBODY:
            # End message section
            self.src.append("</div>")
        else:
            report(f"Internal error: {message_sender} was not handled!")

            if self.current_message_sender != MessageSender.NOBODY:
                # End message section to avoid weird HTML behaviour
                self.src.append("</div>")
                self.current_message_sender = MessageSender.NOBODY
            return

        self.current_message_sender = message_sender

    def is_doing_messages(self) -> bool:
        return self.current_message_sender != MessageSender.NOBODY

    def insert_text(self, content: str):
        if self.raw:
            self.src.append(content)
            self.src.append("\n")
            return

        if self.is_doing_messages():
            if self.current_message_sender == MessageSender.SOTI:
                self.src.append('<span class="message_soti">')
            elif self.current_message_sender == MessageSender.BEBKA:
                self.src.append('<span class="message_bebka">')
            else:
                assert(False)

            self.src.append(content)
            self.src.append("</span>")
        else:
            self.src.append("<p>")
            self.src.append(content)
            self.src.append("</p>")

    def insert_raw_html(self, content: str):
        self.src.append(content)

    def get_baked_src(self) -> str:
        return "".join(self.src)


html_gen: HTMLGen = HTMLGen()


def eat_lines_until_next_meta_directive(rest_of_this_line: str, joiner: str, code: bool = False) -> str:
    lines: list[str] = [rest_of_this_line]

    while True:
        l, status = eat_next_line(code=code)

        if not status:
            break
        if l.startswith("@"):
            return_line()
            break
        lines.append(l)

    return joiner.join(lines)


def expect_eat_until(rest_of_this_line: str, stop: str, joiner: str = "\n", code: bool = False, escapable: bool = False, new_lines: bool = True) -> tuple[str, str, bool]:
    """
    Returns the eaten text, the rest of the final line (if any) and a success flag
    """
    lines: list[str] = []

    l = rest_of_this_line

    escaped_stops = "".join(["\\" + x for x in stop])
    search_pattern = f"(?<!\\\\)(?:\\\\\\\\)*({escaped_stops})"

    while True:
        match = re.search(search_pattern, l)

        if match is None:
            if not new_lines:
                return "", "", False
            else:
                lines.append(l)
                l, status = eat_next_line(code=code)
                if not status:
                    return "", "", False
        else:
            index = match.start()
            lines.append(l[:index])
            l = l[index + len(stop):]
            break

    result = joiner.join(lines)

    search_pattern = f"(\\\\)((?:\\\\\\\\)*)({escaped_stops})"
    result = re.sub(search_pattern, r"\g<2>" + stop, result)
    return result, l, True


def try_parse_meta_directive() -> bool:
    l, status = eat_next_line()
    if not status:
        return False

    rest, status = expect_eat(l, "@")
    if not status:
        report(
            'Expected meta directive on this line. But this line doesn\'t start with "@". Ignoring...')
        return True
    l = rest

    meta_directives: dict[str, Callable[[str], Any]] = {
        "end_meta": lambda rest: rest,  # Dummy
        "lang": lambda rest: languages_dict[rest.lower()],
        "url": lambda rest: rest,
        "title": lambda rest: rest,
        "hide": lambda rest: rest,
        "index": lambda rest: rest,
        "desc": lambda rest: eat_lines_until_next_meta_directive(rest, "<br><br>"),
        "keywords": lambda rest: eat_lines_until_next_meta_directive(rest, ""),
        "tags": lambda rest: eat_lines_until_next_meta_directive(rest, ""),
        "extra_html_head": lambda rest: eat_lines_until_next_meta_directive(rest, "\n", code=True),
        "extra_html_body": lambda rest: eat_lines_until_next_meta_directive(rest, "\n", code=True),
        "content-jupyter": lambda rest: rest,
    }

    rest: str
    status: bool
    directive: str = ""
    for directive, _ in meta_directives.items():
        rest, status = expect_eat(l, directive)
        if status:
            break
    rest = rest.strip()

    if not status:
        report(f'Expected meta directive. Unknown one encountered: "@{l}"')
        report(
            f'Here is a list known ones: @{", @".join(meta_directives.keys())}')
        return False

    # Special treatment
    if directive == "end_meta":
        return False

    meta[directive] = meta_directives[directive](rest)
    return True


article_headers: OrderedDict[str, tuple[int, str]] = OrderedDict()


def str_to_ident(x: str) -> str:
    x = re.sub(r'\W+|^(?=\d)', '_', x.lower())
    return x.strip("_")

def get_header_html_and_save_record(x: str, level: int = 2) -> str:
    ident = str_to_ident(x)

    conditional_arrow_str = "<a href=\"#table_of_contents\"><sup>↑</sup></a>" if "index" in meta else ""
    result = f'<h{level} id="{ident}">{x} {conditional_arrow_str}</h{level}>'

    article_headers[ident] = (level, x)
    return result


def handle_multiline_code(rest: str) -> tuple[str, str, bool]:
    # "rest" here acts as the rest of the line after the "```"
    if len(rest) != 0 and rest != "python":
        report(f'Error: Unsupported language "{rest}" in code directive. ')
        return "", "", False

    rest, status = eat_next_line(code=True)
    if not status:
        return "", "", False

    code, rest, status = expect_eat_until(rest, "```", "\n", code=True)
    if not status:
        report("Error: Unmatched ``` in multiline code directive", True)
        return "", "", False

    result = f'<pre><code class="language-klipse-pyodide">{code}</code></pre>'
    return result, rest, True


def handle_simple_inline(rest: str, stop: str, format: str) -> tuple[str, str, bool]:
    eaten, rest, status = expect_eat_until(
        rest, stop, new_lines=False, escapable=True)
    if not status:
        report(f'Error: Unmatched "{stop}"" in inline formatting', True)
        return "", "", False
    result = format.format(eaten)
    return result, rest, True


annotations: list[str] = []


def handle_note(rest: str) -> tuple[str, str, bool]:
    display, rest, status = handle_simple_inline(rest, stop="]", format="{}")
    if not status:
        return "", "", False

    rest, status = expect_eat(rest, "(")
    if not status:
        report(
            f"Error: Expected a () group for note, which would contain the content, e.g.: #note[display](content)", True)
        return "", "", False

    content, rest, status = handle_simple_inline(rest, stop=")", format="{}")
    if not status:
        return "", "", False

    annotations.append(content)
    id = len(annotations)

    result = f"""<span class="annotation annotation_{id}">
                    <span class="annotation_inline" id="annotation_inline_{id}">{display}</span>
                    <sup><a class="annotation_link" href="#annotation_{id}" style="display:none">{id:02d}</a></sup>
                    <span class="annotation_content" style="display:none">
                        <span class="annotation_bracket">[</span>
                        <span class="annotation_content_raw">{content}</span>
                        <span class="annotation_bracket">]</span>
                    </span>
                </span>"""

    return result, rest, True


def handle_note_link(rest: str) -> tuple[str, str, bool]:
    display, rest, status = handle_simple_inline(rest, stop="]", format="{}")
    if not status:
        return "", "", False

    content = annotations[-1]
    id = len(annotations)

    result = f"""<span class="annotation annotation_{id}">
                    <span class="annotation_inline" id="annotation_inline_{id}">{display}</span>
                    <sup><a class="annotation_link" href="#annotation_{id}" style="display:none">{id:02d}</a></sup>
                    <span class="annotation_content" style="display:none">
                        <span class="annotation_bracket">[</span>
                        <span class="annotation_content_raw">{content}</span>
                        <span class="annotation_bracket">]</span>
                    </span>
                </span>"""

    return result, rest, True

def handle_ext_link(rest: str) -> tuple[str, str, bool]:
    display, rest, status = handle_simple_inline(rest, stop="]", format="{}")
    if not status:
        return "", "", False

    rest, status = expect_eat(rest, "(")
    if not status:
        report(
            f"Error: Expected a () group for external link, which would contain the href, e.g.: #ext_link[display](href)", True)
        return "", "", False

    href, rest, status = handle_simple_inline(rest, stop=")", format="{}")
    if not status:
        return "", "", False

    result = f'<a href="{href}" target="_blank">{display}</a>'
    return result, rest, True


# List of inline formattings and what they do:

# The lambda should return the resulting HTML,
# the rest of the last line read and a status flag.


# Order here matters, because e.g. just a single ` could
# get caught too early without checking for ```.
formattings: OrderedDict[str, Callable[[str],
                                       tuple[str, str, bool]]] = OrderedDict()
formattings["```"] = handle_multiline_code
formattings["`"] = lambda rest: handle_simple_inline(
    rest, stop='`', format="<code>{}</code>")
formattings["#bold("] = lambda rest: handle_simple_inline(
    rest, stop=')', format="<b>{}</b>")
formattings["#italic("] = lambda rest: handle_simple_inline(
    rest, stop=')', format="<em>{}</em>")
formattings["#note["] = lambda rest: handle_note(rest)
formattings["#note_link["] = lambda rest: handle_note_link(rest)
formattings["#ext_link["] = lambda rest: handle_ext_link(rest)

# "#note": lambda x: x,
# "#note_link": lambda x: x,


formattings_first_symbols: str = ""
for k, _ in formattings.items():
    if k[0] not in formattings_first_symbols:
        formattings_first_symbols += k[0]


def handle_inline_formatting(l: str) -> tuple[str, bool]:
    lines: list[str] = []

    while True:
        match = re.search(f"[{formattings_first_symbols}]", l)
        if match is None:
            break

        index = match.start()
        lines.append(l[:index])
        rest = l[index:]

        done: bool = False
        for directive, f in formattings.items():
            if rest.startswith(directive):
                rest, status = expect_eat(rest, directive)
                assert(status)

                html, rest, status = f(rest)
                if not status:
                    return "", False

                lines.append(html)
                done = True
                break

        if not done:
            # False alarm... matched formatting first
            # symbol without it being something we recognize.
            lines.append(rest[0])
            l = rest[1:]
        else:
            l = rest
        continue

    if len(l) != 0:
        lines.append(l)
    return "".join(lines), True


def turn_on_raw() -> str:
    html_gen.raw = True
    return ""


def turn_off_raw() -> str:
    html_gen.raw = False
    return ""


def try_parse_next() -> bool:
    l, status = eat_next_line()
    if not status:
        return False

    # These are short-hand designator for the group chat senders
    rest, status = expect_eat(l, "::")
    if status:
        html_gen.set_message_sender(MessageSender.SOTI)
    else:
        rest, status = expect_eat(l, "##")
        if status:
            html_gen.set_message_sender(MessageSender.BEBKA)

    # If a new message sender has started, see if there is content to be added
    if status:
        rest = rest.strip()
        if len(rest) != 0:
            text, status = handle_inline_formatting(rest)
            if not status:
                return False
            html_gen.insert_text(text)
        return True

    # == means: end message section and start doing normal text again
    _, status = expect_eat(l, "==")
    if status:
        html_gen.set_message_sender(MessageSender.NOBODY)
        return True

    text, status = handle_inline_formatting(l)
    if not status:
        return False

    rest, status = expect_eat(text, "#")
    if not status:
        # Doing normal paragraph...
        html_gen.insert_text(text)
        return True

    # Else: found # at the start, try to handle directive

    text = rest

    # Lists of directives and the html they generate:
    directives: dict[str, Callable[[str], Any]] = {
        "big_header": lambda x: f"<h1>{x}</h1>",
        "header": lambda x: get_header_html_and_save_record(x, level=2),
        "sub_header": lambda x: get_header_html_and_save_record(x, level=3),
        "sub_sub_header": lambda x: get_header_html_and_save_record(x, level=4),
        "sub_sub_sub_header": lambda x: get_header_html_and_save_record(x, level=5),
        "sub_sub_sub_sub_header": lambda x: get_header_html_and_save_record(x, level=6),
        "note": lambda x: f'<span class="note">{x}</span>',
        "center": lambda x: f'<p class="centered">{x}</p>',
        "index": lambda x: f'@INDEX',
        "author": lambda x: f'@AUTHOR',
        "raw": lambda x: turn_on_raw(),
        "no_raw": lambda x: turn_off_raw(),
    }

    status: bool
    directive: str = ""
    for directive, _ in directives.items():
        rest, status = expect_eat(text, directive)
        if status:
            break
    rest = rest.strip()

    if not status:
        report(f'Expected directive. Unknown one encountered: "{l}"')
        report(
            f'Here is a list known ones: #{", #".join(directives.keys())}')
        return False

    text = directives[directive](rest)
    html_gen.insert_raw_html(text)

    return True


def main():
    global lines, line_number

    if len(sys.argv) < 2:
        print("Enter content file name, pleas :)")
        return

    file = sys.argv[1]
    print("Reading... " + file)

    with open(file, "rt", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    if len(lines) == 0:
        print("Opa, empty file")
        return

    if not try_parse_version():
        return

    if version == 1:
        print("Reading older version. Falling back to older script.")
        import generate_article_v1
        generate_article_v1.main()
        return

    if version != 2:
        print("Error: Don't know how to handle dis version ;(")

    # Handling version 2 here:

    doing_meta: bool = True

    while True:
        if doing_meta:
            if try_parse_meta_directive():
                continue
            else:
                doing_meta = False
                report(
                    f"Stopped doing meta directives on this line. Any further ones will get ignored.", True)
                #print("Parsed meta:")
                # for k, v in meta.items():
                #    print(k, "=", v)
                required_meta = ["url", "title", "lang"]
                for r in required_meta:
                    if r not in meta:
                        print(
                            f'Error: Required meta "@{r}" was not set. Stopping parsing.')
                        return

        # Stopped doing meta at this point.. try parsing content for HTMLGen
        if not try_parse_next():
            break

    last_mod_time = date.fromtimestamp(os.path.getmtime(file))
    date_str = get_localized_date_str(last_mod_time)

    ident = meta["url"]
    assert(len(ident) != 0)

    if "hide" in meta:
        shutil.rmtree(f"./{ident}/", ignore_errors=True)
        return
    
    edit_date_str = None

    target_path = f"{ident}/index.html"
    if os.path.exists(target_path):
        with open(target_path, "rt", encoding="utf-8") as target:
            existing_content = target.read()

            match = re.search(
                r'<div class="date">\s*<p>\s*([0-9.]*)', existing_content).group(1)

            edit_date_str = get_localized_last_edit_str(date_str)
            date_str = match

    print(f'Date posted {date_str}')

    template_path = f"post_template.html"
    with open(template_path, "rt", encoding="utf-8") as template:
        content = template.read()

    content = content.replace("@TITLE", meta["title"])
    content = content.replace("@DATE", date_str)
    content = content.replace("@DESC", meta["desc"])
    content = content.replace("@KEYWORDS", meta["keywords"])

    html_tags = ""
    tags_clean = ""
    if "tags" in meta:
        tags = [x.strip() for x in meta["tags"].split(",")]
        tags_clean = ", ".join(tags)
        html_tags = ", ".join([f'<a href="../">{x}</a>' for x in tags])
    content = content.replace("@TAGS_CLEAN", f"TAGS_CLEAN: {tags_clean}")
    content = content.replace("@TAGS", html_tags)

    if edit_date_str is not None:
        content = content.replace("@EDITDATE", edit_date_str)
        print(f"{edit_date_str}")
    else:
        content = content.replace(
            '<div class="edit_date">', '<div class="edit_date" style="visibility: hidden;">')

    content = content.replace(
        '@LANG_META_HTML', get_localized_html_lang_meta_str())

    index_html = ""
    if "index" in meta:
        index_html = '<div class="index"><h3 id="table_of_contents">Table of Contents</h3><ul>'

        last_level: int = 1
        for header_ident, (level, header) in article_headers.items():
            if level > last_level:
                # Push
                index_html += "<ul><li>" * max(0, level - last_level - 1)
                index_html += "<ul>"
            else:
                # Pop as needed (may be 0 pops)
                index_html += "</li></ul>" * (last_level - level)

                index_html += "</li>"

            index_html += f'<li><a href="#{header_ident}">{header}</a>'
            last_level = level

        index_html += "</li></ul></div>"

    content = content.replace("@CONTENT", html_gen.get_baked_src())
    if "content-jupyter" in meta:
        content = content.replace(
            '<div class="content">', '<div class="content-jupyter">')

    content = content.replace("@INDEX", index_html)
    content = content.replace("@EXTRA_HEAD", meta.get("extra_html_head", ""))
    content = content.replace("@EXTRA_BODY", meta.get("extra_html_body", ""))

    author_html = f'<h3 class="author">{get_localized_author_me_str()}</h3>'
    content = content.replace("@AUTHOR", author_html)

    annotations_html = "<ul>"
    for i, a in enumerate(annotations):
        id = i + 1
        annotations_html += f"""<li>
                        <span class="annotation_number" id="annotation_{id}">{id:02d}</span>
                        <span class="annotation_expanded_content">{a} 
                            <a href="#annotation_inline_{id}">↑</a>
                        </span>
                    </li>
                    """
    annotations_html += "</ul>"

    content = content.replace("@ANNOTATIONS", annotations_html)

    os.makedirs(f"./{ident}/", exist_ok=True)
    with open(target_path, "w+", encoding="utf-8") as target:
        target.write(content)

    import generate_index
    generate_index.main(silent=True)


if __name__ == "__main__":
    main()
