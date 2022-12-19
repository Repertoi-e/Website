from typing import Any, Callable, OrderedDict

from enum import Enum

from collections import OrderedDict

import os

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


meta: dict[str, Any] = dict()


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
        "category": lambda rest: rest,
        "css_class": lambda rest: rest,
        "img": lambda rest: rest,
        "title": lambda rest: rest,
        "url": lambda rest: rest,
        "photo_info": lambda rest: rest,
        "desc": lambda rest: eat_lines_until_next_meta_directive(rest, "<br><br>"),
        "tags": lambda rest: eat_lines_until_next_meta_directive(rest, ""),
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

html_gen: str = ""

def try_parse_next() -> bool:
    global html_gen

    l, status = eat_next_line()
    if not status:
        return False

    html_gen = html_gen + l + "\n"
    return True


def get_vault_entry_html_from_meta(m: dict[str, Any]) -> str:
    tags = [f"<div><span>{x.strip()}</span></div>" for x in m.get("tags", "").split(",") if len(x) > 0]

    url = m.get("url", "")
    href = f"href={url}" if len(url) != 0 else ""

    html = f"""                <div class="projects__windows__window {m.get("css_class", "")}">
                    <img src="{m["img"]}">
                    <div class="projects__windows__window__overlay"></div>
                    <a class="projects__windows__window__content" target="_blank" {href}>
                        <h2><span>{m.get("title", "")}</span> {"".join(tags)}</h2>
                        <p>{m.get("desc", "")}</p>
                    </a>
                    <div class="projects__windows__window__photo-info">
                        {m.get("photo_info", "")}
                    </div>
                </div>
    """
    return html

def handle_file(p: str):
    global lines, line_number, meta, html_gen

    with open(p, "rt", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    if len(lines) == 0:
        print("Opa, empty file")
        return
    line_number = 0

    if not try_parse_version():
        return

    if version != 1:
        print("Error: Don't know how to handle dis version ;(")

    doing_meta: bool = True

    while True:
        if doing_meta:
            if try_parse_meta_directive():
                continue
            else:
                doing_meta = False
                #report(
                #    f"Stopped doing meta directives on this line. Any further ones will get ignored.", True)
                #print("Parsed meta:")
                #for k, v in meta.items():
                #    print(k, "=", v)
                required_meta = [ "lang", "img"]
                for r in required_meta:
                    if r not in meta:
                        print(
                            f'Error: Required meta "@{r}" was not set. Stopping parsing.')
                        return

                gen = get_vault_entry_html_from_meta(meta)
                html_gen = html_gen + gen + "\n"
                meta = {}

        # Stopped doing meta at this point.. try parsing content
        if not try_parse_next():
            break

def main():
    for root, _, files in os.walk("./vault"):
        for f in files:
            p = os.path.join(root, f)
            _, ext = os.path.splitext(p)
            if ext == ".ignore":
                continue
            print(p)
            handle_file(p)

    template_path = f"index_template.html"
    with open(template_path, "rt", encoding="utf-8") as template:
        content = template.read()

    html_final = f"""
        <div class="projects__windows">
            <div class="projects__windows__sizer"></div>
            {html_gen}
        </div>
        """
    content = content.replace("@VAULT", html_final)

    with open("./index.html", "w+", encoding="utf-8") as target:
        target.write(content)


if __name__ == "__main__":
    main()
