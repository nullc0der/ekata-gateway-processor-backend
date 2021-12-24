from decimal import Decimal

TX_FIELDS_TO_CHECK = {
    'bitcoin': ['amount', 'txids', 'confirmations'],
    'dogecoin': ['amount', 'txid', 'confirmations'],
    'monero': ['amount', 'txid', 'confirmations'],
    'ethereum': ['value', 'hash'],
    'baza': ['transfers', 'hash']
}

TX_FIELDS_TO_SAVE = {
    'bitcoin': ['amount', 'txids'],
    'dogecoin': ['amount', 'txid'],
    'monero': ['amount', 'txid'],
    'ethereum': ['value', 'hash'],
    'baza': ['transfers', 'hash']
}

CRYPTO_ATOMIC = Decimal('0.00000001')
