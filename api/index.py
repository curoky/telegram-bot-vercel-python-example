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

telegram_app: Optional[TelegramApplication] = None


def setup():
    """ setup logging setting and app """
    logging.basicConfig(level=logging.DEBUG,
                        stream=sys.stdout,
                        force=True,
                        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logging.info('setup start!')
    settings = Dynaconf(environments=True, envvar_prefix=False)
    global telegram_app
    try:
        telegram_app = TelegramApplication.builder().token(settings['TELEGREM_TOKEN']).defaults(
            Defaults(block=True)).build()

        async def echo(update: Update, context) -> None:
            """Echo the user message."""
            await update.message.reply_text(update.message.text)

        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        asyncio.run(telegram_app.initialize())
    except Exception:
        logging.error('setup error: %s', traceback.format_exc())
    logging.info('setup finished!')


async def setup_webhook(request: Request):
    """ setup webhook """
    try:
        if telegram_app:
            web_hook_url = 'telegram-bot-vercel-python-example.vercel.app/api/index'
            res = await telegram_app.bot.delete_webhook(drop_pending_updates=True)
            logging.info('delete_webhook %s', res)
            res = await telegram_app.bot.set_webhook(url=web_hook_url, drop_pending_updates=True)
            logging.info('set_webhook %s', res)
            webhook_info = await telegram_app.bot.get_webhook_info()
            logging.info('get_webhook_info %s', str(webhook_info))
            return Response(content=b'success')
        else:
            return Response(content=b'telegram_app is None')
    except Exception:
        return Response(content=traceback.format_exc().encode('utf8'))


async def receive_update(request: Request):
    """ receive update """
    logging.info('request received!')
    body = await request.body()
    logging.info('request is [%s]', body)
    if telegram_app:
        try:
            update = Update.de_json(json.loads(body), telegram_app.bot)
            if update:
                logging.info('update is: %s)', str(update))
                await telegram_app.process_update(update=update)
            else:
                logging.error('update is None')
        except Exception:
            logging.error('request error: %s', traceback.format_exc(limit=5))
    else:
        logging.error('telegram_app is None')
    logging.info('request finished!')
    return Response(content=b'success')


setup()

app = Starlette(
    debug=True,
    routes=[
        # Route('/', endpoint=index),
        Route('/api/index', endpoint=setup_webhook, methods=['GET']),
        Route('/api/index', endpoint=receive_update, methods=['POST']),
    ])
