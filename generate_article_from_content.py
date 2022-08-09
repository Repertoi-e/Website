import sys

from datetime import date

from bs4 import BeautifulSoup

def main():
	if len(sys.argv) < 2:
		print("Enter content file name and target file name, pleas :)")
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
	version = None # Not used for now, but for future compatibility :)

	doing_paragraph = False

	# Version 1: Either ## (Sotikus) or :: (Bebsikus Il Il)
	doing_messages_from = None 

	line_number = 0

	for l in lines:
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

				title_ident = titles[-1]
				title = " ".join(titles[:-1])

		if last_line.startswith("@End"):
			break

		if last_line.startswith("[["):
			if doing_messages_from is not None:
				# End message section
				html_gen += "</div></div></div>"
				doing_messages_from = None
			doing_paragraph = True
			html_gen += "<p>"
			if len(last_line) <= 2:
				continue
			last_line = last_line[2:]

		if last_line.endswith("]]"):
			if not doing_paragraph:
				print(f"[{line_number}] Unmatched ']]'. We use that for paragraphs! No beginning '[[' did we parse correctly... ")
				return
			if len(last_line) > 2:
				last_line = last_line[:-2]
				html_gen += last_line + "<br>"
			html_gen += "</p>"
			doing_paragraph = False	

		if doing_paragraph:
			html_gen += last_line + "<br>"

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
	d = today.strftime("%d.%m.%Y")

	print(f'Version: {version}, title: "{title}", date: {d}')

	with open("blog_posts/blog_post_template.html", "rt", encoding="utf-8") as template:
		 content = template.read()
	content = content.replace("@TITLE", title)
	content = content.replace("@DATE", d)

	# print(html_gen)
	content = content.replace("@CONTENT", html_gen)

	with open(f"blog_posts/{title_ident}.html", "wt", encoding="utf-8") as target:
		target.write(content)
	
if __name__ == "__main__":
	main()