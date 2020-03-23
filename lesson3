import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
from database.habr_db import HabrDb
from database.models import (
    Post,
    User
)

HEADERS = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}
URL = 'https://habr.com/ru/top/weekly'
BASE_URL = 'https://habr.com'


def get_next_page(soup: BeautifulSoup) -> str:
    return f'{BASE_URL}{soup.find("a", id="next_page")["href"]}'


def get_post_urls(soup: BeautifulSoup) -> set:
    post_links = soup.select('a.post__title_link')
    return set(l['href'] for l in post_links)


def get_post_as_mongo_obj(post_url: str) -> dict:
    response = requests.get(post_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'lxml')

    dt = datetime.strptime(soup.select_one('span.post__time')['data-time_published'], '%Y-%m-%dT%H:%MZ')
    writer = soup.select_one('a.post__user-info span')

    user_links = soup.select('div.comment__head a.user-info')
    users = [{'name': link['data-user-login'], 'url': link['href']} for link in user_links]

    template_data = {'url': post_url,
                     'title': soup.select_one('span.post__title-text').text,
                     'comments_number': soup.find('span', id='comments_count').text.strip(),
                     'publication_date': dt.date(),
                     'publication_time': dt.time(),
                     'writer': {'name': writer.text,
                                'url': writer.parent['href']
                                },
                     'users': users
                     }

    return template_data


def get_post_as_sql_obj(post_url: str) -> Post:
    response = requests.get(post_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'lxml')

    writer_span = soup.select_one('a.post__user-info span')
    writer = User(writer_span.text.strip(), writer_span.parent['href'])
    dt = datetime.strptime(soup.select_one('span.post__time')['data-time_published'], '%Y-%m-%dT%H:%MZ')

    user_links = soup.select('div.comment__head a.user-info')

    user_dict = {link['href']: link['data-user-login'] for link in user_links}

    users = [writer] if user_dict.pop(writer.url, None) else []

    for url, name in user_dict.items():
        users.append(User(name, url))

    post = Post(
        url=post_url,
        name=soup.select_one('span.post__title-text').text.strip(),
        comments_number=soup.find('span', id='comments_count').text.strip(),
        creation_date=dt.date(),
        creation_time=dt.time(),
        writer=writer,
        users=users
    )

    return post


def get_page(url: str):
    while url:
        print(f'Processing page: {url}')
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'lxml')
        yield soup
        url = get_next_page(soup)


response = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(response.text, 'lxml')


def save_to_db():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    finally:
        db.session.close()


# if __name__ == '__main__':
#     client = MongoClient('mongodb://localhost:27017/')
#     db = client['db_blog']
#
#     for soup in get_page(URL):
#         posts = [get_post_as_mongo_obj(url) for url in get_post_urls(soup)]
#
#         db['posts'].insert_many(posts)


if __name__ == '__main__':
    db_url = 'sqlite:///habr_blog.sqlite'
    db = HabrDb(db_url)

    for soup in get_page(URL):

        for url in get_post_urls(soup):
            post = get_post_as_sql_obj(url)

            w_obj = db.session.query(User).filter_by(url=post.writer.url).first()
            if w_obj is None:
                db.session.add(post.writer)
                save_to_db()

            for u in post.users:
                u_obj = db.session.query(User).filter_by(url=u.url).first()
                if u_obj is None:
                    db.session.add(u)
                    save_to_db()

            p_obj = db.session.query(Post).filter_by(url=post.url).first()
            if p_obj is None:
                db.session.add(post)
                save_to_db()

print(1)
