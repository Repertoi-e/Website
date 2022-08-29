import sys

from datetime import date

import bs4.formatter
from bs4 import BeautifulSoup

line_number = 0
version = None # Not used for now (only one version), but for future compatibility :)
lines = None

def report(msg):
	print(f"[{line_number + 1}] {msg}")

def eat_next_line(code = False):
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
			if len(l) == 0: 
				continue
			if l[0] == "#":
				continue
		return l
	return None

def return_line():
	global line_number
	if line_number == 0:
		print("Internal error: returning first line...")
		return
	line_number -= 1

windows = []
window = None

directives = ["css", "title", "controls", "content"]

def expect_window():
	if window is None:
		report(f'No current window for directive. Start a new one with "@x"')
		return False
	return True

def directive(l, symbol):
	if not expect_window(): return None
	if not l.startswith(symbol): return None

	content = ""
	if len(l) > 3:
		l = l[len(symbol):].strip()
		if len(l) != 0:
			if l[0] != ":":
				report("Expected ':' (or nothing else) after the directive")
				return None
			if len(l) > 1:
				l = l[1:].strip()
				content += l + "\n"

	while line_number != len(lines):
		l = eat_next_line()
		if l is None:
			break
		if l[0] == "@": 
			return_line()
			break

		content += l + "\n"

	return content

def try_parse_directive():
	"""
	Returns false on no more lines (or error), otherwise true
	"""
	global windows, window

	l = eat_next_line()
	if l is None: return False

	if l[0] != "@":
		report(f'Unknown line outside of directive: {l}. Directives must start with "@". Current directives: "@x" (infinite repeating Xs for clear separation allowed :P) for new window, "@title", "@css", "@controls", "@content"')
		return False
	
	if len(l) == 1:
		report(f"Empty directive")
		return False

	l = l[1:]
	if l.startswith("x"):
		# print("NEWWINDOW")
		if window is not None:
			windows.append(window)
		
		window = dict()
		return True

	content = None
	for d in directives:
		content = directive(l, d)
		if content is not None:
			# print(d, content)
			window[d] = content
			return True

	if content is None:
		report("Unknown directive")

def try_parse_version():
	global version

	l = eat_next_line()

	if l != "@v1":
		report(f'Unknown version on first line: "{l}". Use something like: @v1')
		return False

	if l == "@v1":
		version = 1
		l = None
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

	while True:
		if not try_parse_directive():
			break
	if window is not None:
		windows.append(window)

	html_gen = ""

	html_template = r"""
	<div class="window_container">
        <div class="window @css">
            <div class="title-bar">
                <div class="title-bar-text">
                    @title
                </div>
                <div class="title-bar-controls">
                    @controls
                </div>
            </div>
            <div class="window-body">
                @content
            </div>
        </div>
    </div>
	"""

	for w in windows:
		gen = html_template
		for d in directives:
			gen = gen.replace(f"@{d}", w.get(d, ""))
		html_gen += gen + "\n"

	template_path = f"index_template.html"
	with open(template_path, "rt", encoding="utf-8") as template:
		content = template.read()
	content = content.replace("@WINDOWSHERE", html_gen)

	formatter = bs4.formatter.HTMLFormatter(indent=4)
	content = BeautifulSoup(content, features="html.parser",).prettify(formatter=formatter)

	#print(content)
 
	target_path = "index.html"
	with open(target_path, "wt", encoding="utf-8") as target:
		target.write(content)
	
if __name__ == "__main__":
	# main()
	pass # under maintenance