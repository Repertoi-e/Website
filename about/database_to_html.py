import json
import os
from bs4 import BeautifulSoup, Comment

with open('database.json', 'r') as json_file:
    data = json.load(json_file)

data.sort(key=lambda x: x.get('order', 0))

with open('index.html', 'r') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')

start_comment = soup.find(string=lambda text: isinstance(text, Comment) and 'BEGIN CONTENT BLOCKS' in text)
end_comment = soup.find(string=lambda text: isinstance(text, Comment) and 'END CONTENT BLOCKS' in text)

# Remove existing content blocks
for tag in start_comment.find_all_next():
    if tag == end_comment:
        break
    tag.decompose()

# Create new content blocks from JSON data
new_blocks = soup.new_tag('div')
for item in data:
    block = soup.new_tag('div', **{'class': 'content__block'})

    if item['type'] == 'video':
        video = soup.new_tag('video', autoplay=True, muted=True, loop=True)
        source = soup.new_tag('source', src=item['src'], type='video/mp4')
        video.append(source)
        block.append(video)
    else:
        img = soup.new_tag('img', src=item['src'])
        block.append(img)

    overlay = soup.new_tag('div', **{'class': 'overlay'})
    block.append(overlay)

    a = soup.new_tag('a', **{'class': 'content__block__content', 'target': '_blank'})
    h2 = soup.new_tag('h2')
    span = soup.new_tag('span')
    h2.append(span)
    a.append(h2)
    p = soup.new_tag('p')
    a.append(p)
    block.append(a)

    photo_info = soup.new_tag('div', **{'class': 'photo-info'})
    photo_info.append(BeautifulSoup(item.get('photo_info', ''), 'html.parser'))
    block.append(photo_info)

    new_blocks.append(block)

start_comment.insert_after(new_blocks)

with open('index.html', 'w') as html_file:
    html_file.write(str(soup.prettify()))
