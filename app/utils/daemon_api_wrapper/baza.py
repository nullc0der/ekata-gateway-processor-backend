from typing import Dict, List, Optional
from decimal import Decimal
import requests

from app.core.config import settings

ATOMIC = Decimal('0.000001')


def from_atomic(amount: int) -> Decimal:
    return (Decimal(amount) * ATOMIC).quantize(ATOMIC)


def to_atomic(amount: Decimal):
    return int(amount * 10 ** 6)


data = {
    'daemonHost': settings.BAZA_COIN_DAEMON_HOST,
    'daemonPort': int(settings.BAZA_COIN_DAEMON_PORT),
    'filename': settings.BAZA_WALLET_FILENAME,
    'password': settings.BAZA_WALLET_PASSWORD
}


class BazaAPIWrapper(object):
    def __init__(self) -> None:
        self.wallet_is_open = False

    def get_request_function(self, req_method):
        if req_method == 'POST':
            return requests.post
        if req_method == 'DELETE':
            return requests.delete
        if req_method == 'PUT':
            return requests.put
        return requests.get

    def get_api_response(self, req_method, api_endpoint, data=None):
        url = settings.BAZA_WALLET_API_URL + api_endpoint
        headers = {
            'X-API-KEY': settings.BAZA_WALLET_API_KEY
        }
        request_function = self.get_request_function(req_method)
        if data:
            return request_function(url, headers=headers, json=data)
        return request_function(url, headers=headers)

    def get_wallet_status(self):
        return self.get_api_response('GET', '/status')

    def open_wallet(self):
        return self.get_api_response('POST', '/wallet/open', data)

    def create_wallet(self):
        return self.get_api_response('POST', '/wallet/create', data)

    def close_wallet(self):
        return self.get_api_response('DELETE', '/wallet')

    def save_wallet(self):
        return self.get_api_response('PUT', '/save')

    def refresh_wallet(self):
        self.get_api_response(
            'PUT', '/reset', data={'scanHeight': 1100000})

    def wallet_is_ready(self):
        res = self.get_wallet_status()
        if res.status_code == 200:
            res_data = res.json()
            if res_data['networkBlockCount'] == res_data['walletBlockCount']:
                return True
        return False

    def get_new_address(self) -> Optional[str]:
        if self.wallet_is_open and self.wallet_is_ready():
            res = self.get_api_response('POST', '/addresses/create')
            self.save_wallet()
            if res.status_code == 201:
                return res.json()['address']

    def validate_address(self, address: str) -> bool:
        if self.wallet_is_open and self.wallet_is_ready():
            res = self.get_api_response(
                'POST', '/addresses/validate', data={'address': address})
            if res.status_code == 200:
                return True
        return False

    def list_transactions(self, address: str) -> Optional[List]:
        if self.wallet_is_open and self.wallet_is_ready():
            # NOTE: We need to cache this value, for MVP it is good, we need to
            # make better solution later
            res = self.get_wallet_status()
            if res.status_code == 200:
                block_count = res.json()['walletBlockCount']
            res = self.get_api_response(
                'GET', f'/transactions/address/{address}/{block_count-500}'
            )
            if res.status_code == 200:
                return res.json()

    def send_to_address(self, address: str, amount: int) -> Optional[Dict]:
        if self.wallet_is_open and self.wallet_is_ready():
            res = self.get_api_response(
                'POST', '/transactions/send/basic',
                data={'destination': address, 'amount': amount})
            if res.status_code == 201:
                return res.json()

    def get_transaction_by_id(self, txid: str) -> Optional[Dict]:
        if self.wallet_is_open and self.wallet_is_ready():
            res = self.get_api_response(
                'GET', f'/transactions/hash/{txid}')
            if res.status_code == 200:
                return res.json()
