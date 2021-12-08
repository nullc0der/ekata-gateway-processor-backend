import json
from decimal import Decimal, ROUND_HALF_UP

from pydantic import UUID4

from app.constants.payment import CRYPTO_ATOMIC
from app.utils.daemon_api_wrapper import daemon_api_wrapper_manager
from app.utils.daemon_api_wrapper.monero import to_atomic


async def task_create_clients_payout_queue(
        ctx, user_id: UUID4, for_currency: str):
    already_exist = await ctx['db'].payout_queues.find_one(
        {'owner_id': user_id, 'for_currency': for_currency})
    if not already_exist:
        await ctx['db'].payout_queues.insert_one(
            {'owner_id': user_id, 'queues': [], 'for_currency': for_currency})


async def task_add_payment_to_payout_queue(ctx, payment_id: str):
    payment = await ctx['db'].payments.find_one({'payment_id': payment_id})
    project = await ctx['db'].projects.find_one(
        {'id': payment['related_project_id']})
    payout_queue = await ctx['db'].payout_queues.find_one(
        {
            'owner_id': project['owner_id'],
            'for_currency': payment['currency_name']
        }
    )
    if payout_queue:
        await ctx['db'].payout_queues.update_one(
            {'_id': payout_queue['_id']},
            {'$push': {'queues': payment['payment_id']}}
        )


async def task_clear_payout_queue(ctx):
    # NOTE: I think a issue will occur, when this task is running and if
    # the task take a lot of time, another will spawn while this runs,
    # what will happen ?
    # We will have current payment queue in new task also and double payout
    # might happen
    # TODO: For monero there is no method to deduct the fee from amount,
    #  also no method to estimate, so we just need to send the total amount,
    # once tx sent, we should save the fee and on later payout
    # we should substract the fee
    payout_queues_cur = ctx['db'].payout_queues.find(
        {'queues': {'$exists': True, '$ne': []}})
    async for payout_queue in payout_queues_cur:
        payments = []
        total_payout_amount = Decimal(0)
        for payment_id in payout_queue['queues']:
            payment = await ctx['db'].payments.find_one(
                {'payment_id': payment_id})
            if payment:
                payments.append(payment)
        for payment in payments:
            total_payout_amount += payment['amount_received']
        payout_address = await ctx['db'].payout_address.find_one(
            {
                'owner_id': payout_queue['owner_id'],
                'currency_name': payout_queue['for_currency']
            }
        )
        if payout_address['payout_address']:
            api_wrapper = daemon_api_wrapper_manager.api_wrappers[
                payout_queue['for_currency']]
            if payout_queue['for_currency'] == 'bitcoin'\
                    or payout_queue['for_currency'] == 'dogecoin':
                txid = api_wrapper.send_to_address(
                    payout_address['payout_address'], total_payout_amount)
            if payout_queue['for_currency'] == 'monero':
                tx_data = api_wrapper.send_to_address(
                    payout_address['payout_address'],
                    to_atomic(total_payout_amount))
                txid = tx_data['tx_hash'] if tx_data else None
            if txid:
                raw_tx_data = api_wrapper.get_transaction_by_id(txid)
                payout_processed_for_payments = [
                    payment['payment_id'] for payment in payments]
                await ctx['db'].payout_queues.update_one(
                    {'_id': payout_queue['_id']},
                    {
                        '$pull': {
                            'queues': {
                                '$in': payout_processed_for_payments
                            }
                        }
                    }
                )
                if payout_queue['for_currency'] == 'bitcoin'\
                        or payout_queue['for_currency'] == 'dogecoin':
                    tx_fee = Decimal(
                        abs(raw_tx_data['fee']) if raw_tx_data else 0)
                if payout_queue['for_currency'] == 'monero':
                    tx_fee = Decimal(0)
                await ctx['db'].payouts.insert_one({
                    'currency_name': payout_queue['for_currency'],
                    'amount': Decimal(
                        total_payout_amount - tx_fee
                    ).quantize(CRYPTO_ATOMIC, ROUND_HALF_UP),
                    'tx_ids': txid,
                    'payout_processed_for_payments':
                    payout_processed_for_payments,
                    'owner_id': payout_queue['owner_id'],
                    'raw_tx_data': json.dumps(raw_tx_data)
                })
