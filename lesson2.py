import requests
from bs4 import BeautifulSoup
from typing import List
from json import dumps
from os import makedirs, path
from urllib.parse import quote


class BaseEntity:
    name: str
    url: str

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def to_json(self) -> str:
        return dumps(self, default=lambda e: e.__dict__, indent=4)


class Writer(BaseEntity):
    def __init__(self, name: str, url: str):
        super(Writer, self).__init__(name, url)


class Tag(BaseEntity):
    def __init__(self, name: str, url: str):
        super(Tag, self).__init__(name, url)


class BlogPost(BaseEntity):
    writer: Writer
    tags: List[Tag]
    image: str

    def __init__(self, name: str, url: str, image: str, writer: Writer, tags: []):
        self.writer = writer
        self.tags = tags
        self.image = image
        super(BlogPost, self).__init__(name, url)


HEADERS = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}
URL = 'https://geekbrains.ru/posts'
BASE_URL = 'https://geekbrains.ru'


def get_next_page(soup: BeautifulSoup) -> str:
    ul = soup.find('ul', attrs={'class': 'gb__pagination'})
    a = ul.find(lambda tag: tag.name == 'a' and tag.text == '›')
    return f'{BASE_URL}{a["href"]}' if a else None


def get_post_url(soup: BeautifulSoup) -> set:
    post_a = soup.select('div.post-items-wrapper div.post-item a')
    return set(f'{BASE_URL}{a["href"]}' for a in post_a)


def get_post(post_url: str) -> BlogPost:
    response = requests.get(post_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'lxml')

    writer_name_el = soup.find('div', attrs={'itemprop': 'author'})

    return BlogPost(
        name=soup.select_one('article h1.blogpost-title').text,
        url=post_url,
        image=soup.select_one('div.blogpost-content img')['src'],
        writer=Writer(writer_name_el.text, f'{BASE_URL}{writer_name_el.parent["href"]}'),
        tags=[Tag(itm.text, f'{BASE_URL}{itm["href"]}') for itm in soup.select('article a.small')]
    )


def get_page(url: str):
    while url:
        print(f'Processing page: {url}')
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'lxml')
        yield soup
        url = get_next_page(soup)


def save_to_json_file(dir_name: str, url_entity: BaseEntity):
    filename = f'{quote(url_entity.url).replace("/", "_")}.json'
    with open(path.join(dir_name, filename), 'w') as file:
        file.write(url_entity.to_json())


response = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(response.text, 'lxml')

blog_posts_dir = 'blog posts'
tags_dir = 'tags'
makedirs(blog_posts_dir, exist_ok=True)
makedirs(tags_dir, exist_ok=True)

# tags_posts = {'tag_name': {'url': '', 'posts': []}}
tags_posts = {}
if __name__ == '__main__':
    for soup in get_page(URL):
        post_urls = get_post_url(soup)
        for url in list(post_urls)[:1]:
            post = get_post(url)
            save_to_json_file(blog_posts_dir, post)

            for tag in post.tags:
                tag_value = tags_posts.get(tag.name, None)
                if tag_value is None:
                    tags_posts[tag.name] = {'url': tag.url, 'posts': [post.url]}
                else:
                    tag_value['posts'].append(post.url)

    with open(path.join(tags_dir, 'tags.json'), 'w') as f:
        f.write(dumps(tags_posts, indent=4))

print(1)
