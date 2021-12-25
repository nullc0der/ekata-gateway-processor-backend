import logging
from typing import Dict

from app.core.config import settings

from app.utils.daemon_api_wrapper.bitcoin import BitcoinAPIWrapper
from app.utils.daemon_api_wrapper.dogecoin import DogeCoinAPIWrapper
from app.utils.daemon_api_wrapper.monero import MoneroAPIWrapper
from app.utils.daemon_api_wrapper.baza import BazaAPIWrapper

logger = logging.getLogger(settings.LOGGER_NAME)


class DaemonApiWrapperManager(object):
    api_wrappers: Dict = {}

    def initialize_api_wrappers(self):
        logger.info("Creating bitcoin wrapper")
        self.api_wrappers['bitcoin'] = BitcoinAPIWrapper(
            settings.BITCOIN_DAEMON_HOST,
            settings.BITCOIN_WALLET_RPC_USERNAME,
            settings.BITCOIN_WALLET_RPC_PASSWORD
        )
        self.api_wrappers['bitcoin'].check_wallet_loaded()
        logger.info("Creating dogecoin wrapper")
        self.api_wrappers['dogecoin'] = DogeCoinAPIWrapper(
            settings.DOGECOIN_DAEMON_HOST,
            settings.DOGECOIN_WALLET_RPC_USERNAME,
            settings.DOGECOIN_WALLET_RPC_PASSWORD
        )
        self.api_wrappers['dogecoin'].check_wallet_loaded()
        if settings.SITE_TYPE == 'production':
            logger.info("Creating monero wrapper")
            self.api_wrappers['monero'] = MoneroAPIWrapper(
                settings.MONERO_DAEMON_HOST,
                settings.MONERO_WALLET_RPC_USERNAME,
                settings.MONERO_WALLET_RPC_PASSWORD
            )
            self.api_wrappers['monero'].check_wallet_loaded()
            logger.info("Creating baza wrapper")
            self.api_wrappers['baza'] = BazaAPIWrapper()
            res = self.api_wrappers['baza'].open_wallet()
            if res.status_code == 403:
                self.api_wrappers['baza'].wallet_is_open = True
            if res.status_code == 400 and res.json()['errorCode'] == 1:
                res = self.api_wrappers['baza'].create_wallet()
            if res.status_code == 200:
                self.api_wrappers['baza'].wallet_is_open = True


daemon_api_wrapper_manager = DaemonApiWrapperManager()
