# -*- coding: utf-8 -*-
import scrapy
import re
import json
from urllib.parse import urljoin, urlencode
from copy import deepcopy


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    graphql_url = 'https://www.instagram.com/graphql/query/?'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    parse_users = ['therock']
    variables = {"id": '',
                 "include_reel": True,
                 "fetch_mutual": False,
                 "first": 100}

    def __init__(self, logpass: tuple, **kwargs):
        self.login, self.pwd = logpass

        self.parsing_methods = {
            'followers': {
                'method': self.parse_followers,
                'query_hash': 'c76146de99bb02f6415203be841dd25a'
            },
            'following': {
                'method': self.parse_following,
                'query_hash': 'd04b0a864b4b54837c0d870b0e77e076'
            },
            'publications': {
                'method': self.parse_publications,
                'query_hash': 'd496eb541e5c789274548bf473cc553e'
            }

        }
        super().__init__(**kwargs)

    def parse(self, response):
        login_url = 'https://www.instagram.com/accounts/login/ajax/'
        csrf_token = self.fetch_csrf_token(response.text)

        yield scrapy.FormRequest(
            login_url,
            method='POST',
            callback=self.main_parse,
            formdata={'username': self.login, 'password':self.pwd},
            headers={'X-CSRFToken': csrf_token}
        )

    def main_parse(self, response):
        j_resp = json.loads(response.text)
        if j_resp.get('authenticated'):
            for u_name in self.parse_users:
                yield response.follow(
                    urljoin(self.start_urls[0], u_name),
                    callback=self.parse_user,
                    cb_kwargs={'user_name': u_name}
                )

    def parse_user(self, response, user_name: str):
        user_id = self.fetch_user_id(response.text, user_name)
        user_vars = deepcopy(self.variables)
        user_vars.update({'id': user_id})

        parsing_method = self.parsing_methods['publications']

        url = self.make_graphql_url(user_vars, query_hash=parsing_method['query_hash'])
        yield response.follow(
            url,
            callback=parsing_method['method'],
            cb_kwargs={'user_vars': user_vars, 'user_name': user_name}
        )

    def parse_followers(self, response, user_vars, user_name):
        j_response = json.loads(response.text)
        if j_response['data']['user']['edge_followed_by']['page_info']['has_next_page']:
            user_vars.update({'after': j_response['data']['user']['edge_followed_by']['page_info']['end_cursor']})
            url = self.make_graphql_url(user_vars, query_hash=self.parsing_methods['followers']['query_hash'])
            yield response.follow(
                url,
                callback=self.parse_followers,
                cb_kwargs={'user_vars': user_vars, 'user_name': user_name}
            )

        followers = j_response['data']['user']['edge_followed_by']['edges']

        for follower in followers:
            yield {
                'user_name': user_name,
                'user_id': user_vars['id'],
                'follower': follower['node']
            }

    def parse_following(self, response, user_vars, user_name):
        j_response = json.loads(response.text)
        if j_response['data']['user']['edge_follow']['page_info']['has_next_page']:
            user_vars.update({'after': j_response['data']['user']['edge_follow']['page_info']['end_cursor']})
            url = self.make_graphql_url(user_vars, query_hash=self.parsing_methods['following']['query_hash'])
            yield response.follow(
                url,
                callback=self.parse_followers,
                cb_kwargs={'user_vars': user_vars, 'user_name': user_name}
            )

        following = j_response['data']['user']['edge_follow']['edges']

        for f in following:
            yield {
                'user_name': user_name,
                'user_id': user_vars['id'],
                'following': f['node']
            }

    def parse_publications(self, response, user_vars, user_name):
        j_response = json.loads(response.text)
        if j_response['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']:
            user_vars.update({'after': j_response['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']})
            url = self.make_graphql_url(user_vars, query_hash=self.parsing_methods['publications']['query_hash'])
            yield response.follow(
                url,
                callback=self.parse_publications,
                cb_kwargs={'user_vars': user_vars, 'user_name': user_name}
            )

        publications = j_response['data']['user']['edge_owner_to_timeline_media']['edges']

        for publication in publications:
            yield {
                'user_name': user_name,
                'user_id': user_vars['id'],
                'publication': publication['node']
            }

    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, user_name: str):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % user_name, text
        ).group()
        return json.loads(matched).get('id')

    def make_graphql_url(self, user_vars, query_hash):
        return f'{self.graphql_url}query_hash={query_hash}&{urlencode(user_vars)}'
