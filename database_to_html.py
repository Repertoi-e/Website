import json
import os 

import cv2

from bs4 import BeautifulSoup, Comment
from PIL import Image
from moviepy.editor import VideoFileClip

with open('database.json', 'r') as json_file:
    data = json.load(json_file)

data.sort(key=lambda x: x.get('order', 0))

def reverse_sort_chunks(data, chunk_size=3):
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    reversed_chunks = [chunk[::-1] for chunk in chunks]
    return [item for sublist in reversed_chunks for item in sublist]

data = reverse_sort_chunks(data)

with open('index.html', 'r') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')

start_comment = soup.find(string=lambda text: isinstance(text, Comment) and 'BEGIN CONTENT BLOCKS' in text)
end_comment = soup.find(string=lambda text: isinstance(text, Comment) and 'END CONTENT BLOCKS' in text)

# Remove existing content blocks
for tag in start_comment.find_all_next():
    if tag == end_comment:
        break
    tag.decompose()

def get_dimensions(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in ['.png', '.jpg', '.jpeg', '.gif']:
        with Image.open(file_path) as img:
            width, height = img.size
            return width, height
    elif file_ext in ['.mp4', '.mov']:
        clip = VideoFileClip(file_path)
        width, height = clip.size
        clip.close()
        return width, height
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

def resize_to_max_dimension(width, height, max_dimension=1000):
    if width > height:
        scale = max_dimension / float(width)
    else:
        scale = max_dimension / float(height)
    return int(width * scale), int(height * scale)

# Create new content blocks from JSON data
new_blocks = soup.new_tag('div')
for item in data:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    width, height = resize_to_max_dimension(*get_dimensions(os.path.join(script_dir, './' + item['src'])))

    block_attrs = {
        'class': 'content__block', 
        'href': item['src'],
        'data-pswp-width': width,
        'data-pswp-height': height,
        'target': '_blank'
    }
    if item['type'] == 'video': block_attrs['data-pswp-type'] = 'video'

    block = soup.new_tag('a', **block_attrs)
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

    content = soup.new_tag('div', **{'target': '_blank'})
    h2 = soup.new_tag('h2')
    span = soup.new_tag('span')
    h2.append(span)
    content.append(h2)
    p = soup.new_tag('p')
    content.append(p)
    block.append(content)

    photo_info = soup.new_tag('div', **{'class': 'photo-info'})
    photo_info.append(BeautifulSoup(item.get('photo_info', ''), 'html.parser'))
    block.append(photo_info)

    new_blocks.append(block)

start_comment.insert_after(new_blocks)

with open('index.html', 'w') as html_file:
    html_file.write(str(soup))
