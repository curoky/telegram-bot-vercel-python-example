# Copyright (c) 2023-2023 curoky(cccuroky@gmail.com).
#
# This file is part of telegram-bot-vercel-python-example.
# See https://github.com/curoky/telegram-bot-vercel-python-example for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import logging
import sys
import traceback
from typing import Optional

from dynaconf import Dynaconf
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application as TelegramApplication
from telegram.ext import Defaults, MessageHandler, filters

# https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/customwebhookbot.py


def create_bot(token: str) -> Optional[TelegramApplication]:
    """ create_telegram_app """

    logging.info('create_telegram_app start!')
    try:
        tgbot = TelegramApplication.builder().token(token).defaults(Defaults(block=True)).build()

        async def echo(update: Update, context) -> None:
            """Echo the user message."""
            await update.message.reply_text(update.message.text)

        tgbot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        asyncio.run(tgbot.initialize())
        return tgbot
    except Exception:
        logging.error('create_telegram_app error: %s', traceback.format_exc())
    return None


async def setup_webhook(request: Request):
    """ setup webhook """
    if bot:
        try:
            web_hook_url = 'telegram-bot-vercel-python-example.vercel.app/api/index'
            res = await bot.bot.delete_webhook(drop_pending_updates=True)
            logging.info('delete_webhook %s', res)
            res = await bot.bot.set_webhook(url=web_hook_url, drop_pending_updates=True)
            logging.info('set_webhook %s', res)
            webhook_info = await bot.bot.get_webhook_info()
            logging.info('get_webhook_info %s', str(webhook_info))
            return Response(content=b'success')
        except Exception:
            return Response(content=traceback.format_exc().encode('utf8'))
    else:
        return Response(content=b'telegram_app is None')


async def receive_update(request: Request):
    """ receive update """
    logging.info('request received!')
    body = await request.body()
    logging.info('request is [%s]', body)
    if bot:
        try:
            update = Update.de_json(json.loads(body), bot.bot)
            if update:
                logging.info('update is: %s)', str(update))
                await bot.process_update(update=update)
            else:
                logging.error('update is None')
        except Exception:
            logging.error('request error: %s', traceback.format_exc(limit=5))
    else:
        logging.error('telegram_app is None')
    logging.info('request finished!')
    return Response(content=b'success')


logging.basicConfig(level=logging.DEBUG,
                    stream=sys.stdout,
                    force=True,
                    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')

settings = Dynaconf(environments=True, envvar_prefix=False)

bot = create_bot(token=settings['TELEGREM_TOKEN'])

app = Starlette(
    debug=True,
    routes=[
        # Route('/', endpoint=index),
        Route('/api/index', endpoint=setup_webhook, methods=['GET']),
        Route('/api/index', endpoint=receive_update, methods=['POST']),
    ])
