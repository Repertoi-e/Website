import sys

from datetime import date

from bs4 import BeautifulSoup

import os.path
import re 

def main():
	if len(sys.argv) < 2:
		print("Enter content file name, pleas :)")
		return

	file = sys.argv[1]
	print("Reading... " + file)

	with open(file, "rt", encoding="utf-8") as f:
		content = f.read()
	
	lines = content.split("\n")

	html_gen = ""

	last_line = None

	title = None
	title_ident = None
	desc = None
	keywords = None
	version = None # Not used for now, but for future compatibility :)

	doing_paragraph = False
	doing_python = False

	# Version 1: Either ## (Sotikus) or :: (Bebsikus Il Il)
	doing_messages_from = None 

	line_number = 0

	lang_en = False

	for l in lines:
		if not doing_python: 
			l = l.strip()
		line_number += 1
		if last_line is None and len(l) == 0: continue
		
		last_line = l

		if version is None:
			if last_line != "@v1":
				print(f'[{line_number}] Unknown version on first line: "{last_line}". Use something like: @v1')
				return

			if last_line == "@v1":
				version = 1
				last_line = None
				continue

		if title is None:
			if not last_line.startswith("@Begin "):
				print(f"[{line_number}] Expected a @Begin statement with the article title..")
				return
			else:
				titles = last_line[6:].strip()
				titles = titles.split()
				if titles[0] == "[EN]":
					lang_en = True
					titles = titles[1:]

				title_ident = titles[-1]
				title = " ".join(titles[:-1])
				continue

		if desc is None:
			if not last_line.startswith("@Desc "):
				print(f"[{line_number}] Expected a @Desc statement with the article description..")
				return
			else:
				desc = last_line[6:].strip()
				continue

		if keywords is None:
			if not last_line.startswith("@Keywords "):
				print(f"[{line_number}] Expected a @Keywords statement with the article keywords..")
				return
			else:
				keywords = last_line[10:].strip()
				continue

		if last_line.startswith("@End"):
			break
		 
		paragraph_centered = last_line.startswith("[[cent")
		if paragraph_centered or last_line.startswith("[["):
			if doing_messages_from is not None:
				# End message section
				html_gen += "</div></div></div>"
				doing_messages_from = None
			doing_paragraph = True
			if paragraph_centered:
				html_gen += '<p class="cent">'
			else:
				html_gen += "<p>"
			if len(last_line) <= 2:
				continue
			if paragraph_centered:
				last_line = last_line[6:]
			else:
				last_line = last_line[2:]

		if last_line.startswith("[py"):
			if doing_messages_from is not None:
				# End message section
				html_gen += "</div></div></div>"
				doing_messages_from = None
			doing_python = True
			html_gen += '<pre><code class="language-klipse-pyodide">\n'
			if len(last_line) <= 3:
				continue
			last_line = last_line[3:]

		if last_line.endswith("]]"):
			if not doing_paragraph and not doing_python:
				print(f"[{line_number}] Unmatched ']]'. We use that for paragraphs! No beginning '[[' did we parse correctly... ")
				return
			if len(last_line) > 2:
				last_line = last_line[:-2]
				html_gen += last_line + "<br>"
			if doing_paragraph:
				html_gen += "</p>"
				doing_paragraph = False	
			if doing_python:
				html_gen += "\n</code></pre>"
				doing_python = False	
				
		if doing_paragraph:
			html_gen += last_line + "<br>"
		elif doing_python:
			html_gen += last_line + "\n"
		#elif len(last_line) != 0:
		#	print(f"[{line_number}] Skipping non-empty line: {last_line}")

		if last_line.startswith("##"):
			if doing_paragraph:
				print(f"[{line_number}] Found ## while still doing paragraph!")
				return
			if doing_messages_from is None:
				html_gen += '<div class="message_section">'
			else:
				# End old recipient
				html_gen += "</div></div>"
			doing_messages_from = "##"
			html_gen += '<div class="message_soti_div"><div class="message_soti_container">'
			if len(last_line) <= 2:
				continue
			last_line = last_line[2:]

		if last_line.startswith("::"):
			if doing_paragraph:
				print(f"[{line_number}] Found :: while still doing paragraph!")
				return
			if doing_messages_from is None:
				html_gen += '<div class="message_section">'
			else:
				# End old recipient
				html_gen += "</div></div>"
			doing_messages_from = "::"
			html_gen += '<div class="message_bilil_div"><div class="message_bilil_container">'
			if len(last_line) <= 2:
				continue
			last_line = last_line[2:]

		if doing_messages_from == "##":
			if len(last_line) == 0: continue
			html_gen += f'<span class="message_soti">{last_line}</span>'

		if doing_messages_from == "::":
			if len(last_line) == 0: continue
			html_gen += f'<span class="message_bilil">{last_line}</span>'

	if last_line is None:
		print("Opa, empty file")
		return

	html_gen = BeautifulSoup(html_gen, features="html.parser").prettify()

	today = date.today()
	date_string = today.strftime("%d.%m.%Y" if lang_en else "%d.%m.%Y г.")
	edit_date_string = None

	target_path = f"post/{title_ident}/index.html"
	if os.path.exists(target_path):
		with open(target_path, "rt", encoding="utf-8") as target:
			existing_content = target.read()
			
			match = re.findall(r'<div class="date">\s*<p>([0-9.]*)', existing_content)
			
			edit_date_string = f"Last edited {date_string}" if lang_en else f"Последна редакция {date_string}"
			date_string = match[0]

	print(f'Version: {version}, title: "{title}", date: {date_string}, edit date (today): {edit_date_string}')

	template_path = f"post_template.html"
	with open(template_path, "rt", encoding="utf-8") as template:
		content = template.read()
	content = content.replace("@TITLE", title)
	content = content.replace("@DATE", date_string)
	content = content.replace("@DESC", desc)
	content = content.replace("@KEYWORDS", keywords)
	content = content.replace("@AUTHOR", "Dimitar Sotirov" if lang_en else "Димитър Сотиров")
	if edit_date_string is not None:
		content = content.replace("@EDITDATE", edit_date_string)
	else:
		content = content.replace('<div class="edit_date">', '<div class="edit_date" style="visibility: hidden;">')

	if not lang_en:
		content = content.replace('<html lang="en-GB">', '<html lang="bg">')

	# print(html_gen)
	content = content.replace("@CONTENT", html_gen)

	with open(target_path, "w+", encoding="utf-8") as target:
		target.write(content)
	
if __name__ == "__main__":
	main()