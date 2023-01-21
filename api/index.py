# Copyright (c) 2018-2022 curoky(cccuroky@gmail.com).
#
# This file is part of my-own-x.
# See https://github.com/curoky/my-own-x for further info.
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
import logging
from typing import Optional

from dynaconf import Dynaconf
from sanic import Sanic
from sanic.response import HTTPResponse
from telegram import Bot, Update
from telegram.ext import Application as TelegramApplication

telegram_app: Optional[TelegramApplication] = None


async def setup_webhook(bot: Bot):
    web_hook_url = 'telegram-bot-vercel-python-example.vercel.app/api/index'
    res = await bot.delete_webhook(drop_pending_updates=True)
    logging.info('delete_webhook %s', res)
    res = await bot.set_webhook(url=web_hook_url, drop_pending_updates=True)
    logging.info('set_webhook %s', res)
    webhook_info = await bot.get_webhook_info()
    logging.info('get_webhook_info %s', str(webhook_info))


def setup():
    logging.basicConfig(level=logging.INFO)
    logging.info('setup start!')

    settings = Dynaconf(environments=True, envvar_prefix=False)
    global telegram_app
    telegram_app = TelegramApplication.builder().token(settings['TELEGREM_TOKEN']).build()

    asyncio.run(setup_webhook(telegram_app.bot))

    logging.info('setup finished!')


setup()

app = Sanic()


@app.route('/')
async def index(request):
    logging.info('request received!')
    logging.info('request is [%s]', str(request))
    if telegram_app:
        update = Update.de_json(request, telegram_app.bot)
        if update:
            logging.info('update is: [%s][%s])', update.message.from_user.name, update.message)
            await telegram_app.process_update(update=update)
        else:
            logging.error('update is None')
    else:
        logging.error('telegram_app is None')
    logging.info('request finished!')
    return HTTPResponse()
