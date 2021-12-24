import requests
from requests.exceptions import ConnectionError
from bson import ObjectId

import simplejson as json

from app.core.config import settings
from app.models.payments import Payment

# TODO: send email after a payout is done


async def task_sync_currency_price(ctx):
    data = {}
    for currency in settings.ALLOWED_CURRENCY_NAME:
        try:
            if currency == 'baza':
                res = requests.get(
                    'https://www.southxchange.com/api/price/BAZA/TUSD')
                if res.status_code == 200:
                    data[currency] = {'usd': res.json()['Last']}
                else:
                    data[currency] = {}
            else:
                res = requests.get(
                    'https://api.coingecko.com/api/v3/simple/'
                    f'price?ids={currency}&vs_currencies=usd')
                if res.status_code == 200:
                    data[currency] = res.json().get(currency, {})
                else:
                    data[currency] = {}
        except ConnectionError:
            data[currency] = {}
    await ctx['redis_client'].set('currency_price', json.dumps(data))


async def task_send_payment_data_to_webhook(
        ctx, payment_id: str, signature: str):
    payment = await ctx['db'].payments.find_one({'payment_id': payment_id})
    project = await ctx['db'].projects.find_one(
        {'id': payment['related_project_id']})
    if project['webhook_url']:
        requests.post(
            project['webhook_url'],
            data=Payment(
                **payment,
                signature=signature,
                created_on=ObjectId(payment['_id']).generation_time
            ).json(),
            headers={
                'Content-Type': 'application/json'
            }
        )
