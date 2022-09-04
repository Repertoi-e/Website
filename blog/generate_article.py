from typing import Any, Callable
import sys

from enum import Enum

from datetime import date

import re
import os.path

import bs4

line_number: int = 0
version: int = 0
lines: list[str] = []


def report(msg: str):
    print(f"[{line_number + 1}] {msg}")


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
            l = l.strip()
            if len(l) == 0:  # Ignore regular empty lines
                continue
            if l.startswith("//"):  # Ignore comments
                continue
        return l, True
    return "", False


def return_line():
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
    return "Dimitar Sotirov" if meta["lang"] == Language.ENGLISH else "Димитър Сотиров"

def get_localized_html_lang_meta_str() -> str:
    return '<html lang="en-GB">' if meta["lang"] == Language.ENGLISH else '<html lang="bg">'


class HTMLGen():
    src: list[str] = []

    current_message_sender: MessageSender = MessageSender.NOBODY

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


def eat_lines_until_code_stop(rest_of_this_line: str, joiner: str = "\n", code: bool = False) -> str:
    lines: list[str] = [rest_of_this_line]

    while True:
        l, status = eat_next_line(code=code)

        if not status:
            break
        if l.startswith("```"):
            # Don't return line.. instead parsing continues as normal from next
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
        "end_meta": lambda x: x,  # Dummy
        "lang": lambda x: languages_dict[x.lower()],
        "url": lambda x: x,
        "title": lambda x: x,
        "desc": lambda x: eat_lines_until_next_meta_directive(x, "<br><br>"),
        "keywords": lambda x: eat_lines_until_next_meta_directive(x, ""),
        "extra_html_head": lambda x: eat_lines_until_next_meta_directive(x, "\n", code=True),
        "extra_html_body": lambda x: eat_lines_until_next_meta_directive(x, "\n", code=True)
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
            html_gen.insert_text(rest)
        return True

    # == means: end message section and start doing normal text again
    _, status = expect_eat(l, "==")
    if status:
        html_gen.set_message_sender(MessageSender.NOBODY)
        return True

    rest, status = expect_eat(l, "#")
    if not status:
        # Doing normal paragraph...
        html_gen.insert_text(l)
        return True

    # Else: try doing directive

    l = rest

    # Lists of directives and the html they generate:
    directives: dict[str, Callable[[str], Any]] = {
        "section_header": lambda x: f"<h4>{x}</h4>",
        "note": lambda x: f'<span class="note">{x}</span>',
        "center": lambda x: f'<p class="centered">{x}</p>',
        "```python": lambda x: f'<pre><code class="language-klipse-pyodide">{eat_lines_until_code_stop(x, code=True)}</code></pre>',
    }

    status: bool
    directive: str = ""
    for directive, _ in directives.items():
        rest, status = expect_eat(l, directive)
        if status:
            break
    rest = rest.strip()

    if not status:
        report(f'Expected directive. Unknown one encountered: "#{l}"')
        report(
            f'Here is a list known ones: #{", #".join(directives.keys())}')
        return False

    text = directives[directive](rest)
    html_gen.insert_raw_html(text)

    return True


def main():
    global lines, line_number, windows

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
                print(
                    f"Stopped doing meta directives on line {line_number}. Any further ones will get ignored.")
                print("Parsed meta:")
                for k, v in meta.items():
                    print(k, "=", v)
                required_meta = ["url", "title", "lang"]
                for r in required_meta:
                    if r not in meta:
                        print(
                            f'Error: Required meta "@{r}" was not set. Stopping parsing.')
                        return

        # Stopped doing meta at this point.. try parsing content for HTMLGen
        if not try_parse_next():
            break

    today = date.today()
    date_str = get_localized_date_str(today)

    ident = meta["url"]
    assert(len(ident) != 0)

    edit_date_str = None

    target_path = f"{ident}/index.html"
    if os.path.exists(target_path):
        with open(target_path, "rt", encoding="utf-8") as target:
            existing_content = target.read()
            
            match = re.findall(r'<div class="date">\s*<p>\s*([0-9.]*)', existing_content)
            
            edit_date_str = get_localized_last_edit_str(date_str)
            date_str = match[0]

    print(f'Date posted {date_str}')

    template_path = f"post_template.html"
    with open(template_path, "rt", encoding="utf-8") as template:
        content = template.read()

    content = content.replace("@TITLE", meta["title"])
    content = content.replace("@DATE", date_str)
    content = content.replace("@DESC", meta["desc"])
    content = content.replace("@KEYWORDS", meta["keywords"])
    content = content.replace("@AUTHOR", get_localized_author_me_str())
    
    if edit_date_str is not None:
        content = content.replace("@EDITDATE", edit_date_str)
        print(f"{edit_date_str}")
    else:
        content = content.replace('<div class="edit_date">', '<div class="edit_date" style="visibility: hidden;">')

    content = content.replace('@LANG_META_HTML', get_localized_html_lang_meta_str())

    content = content.replace("@CONTENT", html_gen.get_baked_src())
    content = content.replace("@EXTRA_HEAD", meta.get("extra_html_head", ""))
    content = content.replace("@EXTRA_BODY", meta.get("extra_html_body", ""))

    formatter = bs4.formatter.HTMLFormatter(indent=4)
    content = bs4.BeautifulSoup(content, features="html.parser").prettify(formatter=formatter)

    with open(target_path, "w+", encoding="utf-8") as target:
        target.write(content)


if __name__ == "__main__":
    main()
