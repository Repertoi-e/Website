import os

import re

import sys

from datetime import datetime

def main(silent: bool = False):
    if not silent:
        if len(sys.argv) > 2:
            print("Usage: generate_index.py [regen]")
            return
        
        if len(sys.argv) == 2:
            if sys.argv[1] != "regen":
                print("Usage: generate_index.py [regen]")
                return
            else:
                # get all .txt files in ./content/
                for subdir, dirs, files in os.walk("./"):
                    for f in files:
                        if f.endswith(".txt"):
                            p = os.path.join(subdir, f)
                            if os.path.exists(os.path.join(p, "ignore")): continue
                            os.system(f"python3 generate_article.py \"{p}\"")

    print("--- Generating index.html")

    template_path = f"index_template.html"
    with open(template_path, "rt", encoding="utf-8") as template:
        content = template.read()

    articles: list[tuple[str, str, str, str]] = []

    for subdir, dirs, _ in os.walk("./"):
        for d in dirs:
            p = os.path.join(subdir, d)
            if os.path.exists(os.path.join(p, "ignore")): continue

            article_html_path = os.path.join(p, "index.html")
            with open(article_html_path, "rt", encoding="utf-8") as article:
                article_html = article.read()

            date = re.search(r'<div class="date">\s*<p>\s*([0-9.]*)', article_html).group(1)
            title = re.search(r"<title>(.*) \| .*</title>", article_html).group(1)
            tags = re.search(r'<!-- TAGS_CLEAN: (.*) -->', article_html).group(1).split(", ")
            if not silent: print(d)

            tags_html = ""
            for t in tags:
                if len(t) == 0: continue
                tags_html += f'<div><span>{t}</span></div>\n'

            articles.append((tags_html, d, title, date))

    article_links_html = ""

    def get_int_from_time(x: str):
        d = datetime.strptime(x, "%d.%m.%Y")
        return int(d.strftime("%Y%m%d"))

    for tags_html, link, title, date in sorted(articles, key=lambda x: get_int_from_time(x[3]), reverse=True):
        html = f"""<div class="article-links__link">
                <div>
                    <div class="article-links__link__tags">
                        {tags_html}
                    </div>
                    <span class="article-links__link__title">
                        <span>⟶</span>
                        <a href="./{link}/">
                            <h3>{title}</h3>
                        </a>
                    </span>
                </div>
                <span>
                    <p>
                        {date}
                    </p>
                </span>
            </div>
            """

        article_links_html += html

    content = content.replace("@ARTICLE_LINKS", article_links_html) 

    with open("index.html", "w+", encoding="utf-8") as target:
        target.write(content) 

if __name__ == "__main__":
    main()
