import requests
import json
import time
import os

URL_SPECIAL_OFFERS = 'https://5ka.ru/api/v2/special_offers/'
URL_CATEGORIES = 'https://5ka.ru/api/v2/categories/'

HEADERS = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }


def get_data_by_url(url, headers):
    response = requests.get(url, headers=headers)

    if response.status_code // 100 != 2:
        return None

    return response.json()


def get_products_by_category(url, headers, category, ):
    records_per_page = 20
    page_counter = 1

    records = []

    is_next_page = True

    while is_next_page:
        url = f'{url}?categories={category}&records_per_page={records_per_page}&page={page_counter}'

        data = get_data_by_url(url, headers)

        if data is None:
            return records

        records.extend(data.get('results'))
        is_next_page = data.get('next') is not None
        page_counter += 1
        time.sleep(1)

    return records


if __name__ == '__main__':
    categories = get_data_by_url(URL_CATEGORIES, HEADERS)

    products_dir = 'Products'
    os.makedirs(products_dir, exist_ok=True)

    for c in categories:
        products = get_products_by_category(URL_SPECIAL_OFFERS, HEADERS, c.get('parent_group_code'))

        if len(products) > 0:

            category_name_ar = c.get("parent_group_name")\
                .replace('*\n*', '')\
                .replace('"', '')\
                .lower()\
                .split()
            category_name_ar[0] = category_name_ar[0].title()
            category_name = ' '.join(category_name_ar)

            with open(f'{products_dir}\\{category_name}.json', 'w') as file:
                file.write(json.dumps(products))