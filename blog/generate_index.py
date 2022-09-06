import os

import re

def main(silent: bool = False):
    template_path = f"index_template.html"
    with open(template_path, "rt", encoding="utf-8") as template:
        content = template.read()

    article_links_html = ""

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
                tags_html += f'<div class="tag"><span>{t}</span></div>\n'

            html = f"""<div class="article_link">
                <div class="title_and_tags">
                    <div class="tags">
                        {tags_html}
                    </div>
                    <span class="title">
                        <span class="title_arrow">⟶</span>
                        <a href="./{d}/">
                            <h3>{title}</h3>
                        </a>
                    </span>
                </div>
                <span class="date">
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
