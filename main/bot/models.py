from typing import List
import requests
from requests.auth import HTTPBasicAuth
from bot import settings


class Bot:
    @classmethod
    def _requestget(cls, url, params=None, data=None):
        return requests.get(url, params, auth=HTTPBasicAuth(settings.WEB_LOGIN, settings.WEB_PASSWORD))

    @classmethod
    def _requestput(cls, url, data=None):
        return requests.put(url, data, auth=HTTPBasicAuth(settings.WEB_LOGIN, settings.WEB_PASSWORD))

    @classmethod
    def _requestpost(cls, url, data):
        return requests.post(url, data, auth=HTTPBasicAuth(settings.WEB_LOGIN, settings.WEB_PASSWORD))

    @classmethod
    def get_user(cls, telegram_id:str) -> dict:
        response = cls._requestget(f'{settings.URL_API}users/{telegram_id}')
        if response.status_code == 200:
            return response.json()
        else:
            return {}

    @classmethod
    def get_peer(cls, peer_id:int) -> dict:
        response = cls._requestget(f'{settings.URL_API}peers/{peer_id}')
        if response.status_code == 200:
            return response.json()
        else:
            return {}

    @classmethod
    def get_peers_of_user(cls, telegram_id:str) -> list:
        response = cls._requestget(f'{settings.URL_API}peers_of_user/{telegram_id}')
        if response.status_code == 200:
            return response.json()
        else:
            return []

    @classmethod
    def check_user_for_adding_peer(cls, telegram_id:str) -> list:
        PARAMS = {'type': 'check_add_peer'}
        response = cls._requestget(f'{settings.URL_API}users/{telegram_id}', params=PARAMS)
        if response.status_code == 200:
            return response.json()
        else:
            return {}

    @classmethod
    def get_config(cls, telegram_id:str, peer_id:int):
        PARAMS = {'type': 'download', 'peer_id': peer_id}
        response = cls._requestget(f'{settings.URL_API}users/{telegram_id}', params=PARAMS)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    @classmethod
    def get_dns(cls, telegram_id:str) -> list:
        PARAMS = {'telegram_id': telegram_id}
        response = cls._requestget(f'{settings.URL_API}dns/', params=PARAMS)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    @classmethod
    def set_dns(cls, peer_id:int, dns_id:int) -> dict:
        data = {'dns_id': dns_id}
        response = cls._requestput(f'{settings.URL_API}peers/{peer_id}', data=data)
        if response.status_code == 201:
            return response.json()
        else:
            return []

    @classmethod
    def get_allowed_networks(cls) -> list:
        response = cls._requestget(f'{settings.URL_API}allowed_networks/')
        if response.status_code == 200:
            return response.json()
        else:
            return {}

    @classmethod
    def set_allowed_networks(cls, peer_id:int, allowed_networks_id:int) -> dict:
        data = {'allowed_networks_id': allowed_networks_id}
        response = cls._requestput(f'{settings.URL_API}peers/{peer_id}', data=data)
        if response.status_code == 201:
            return response.json()
        else:
            return {}

    @classmethod
    def update_keys(cls, peer_id:int,) -> dict:
        data = {'update_keys': True}
        response = cls._requestput(f'{settings.URL_API}peers/{peer_id}', data=data)
        if response.status_code == 201:
            return response.json()
        else:
            return {}

    @classmethod
    def make_excess_peer(cls, telegram_id:str) -> dict:
        data = {'telegram_id': telegram_id}
        response = cls._requestpost(f'{settings.URL_API}peers/', data=data)
        if response.status_code == 201:
            return response.json()
        else:
            return []
