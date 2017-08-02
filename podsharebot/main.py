# coding: utf-8

import os
import inspect
import logging
from telegram.ext import Updater, Filters
from telegram.ext import CommandHandler, MessageHandler


CMD_NAME_KEY = 'cmd_name'
HANDLER_CLS_KEY = 'handler_cls'
HANDLER_ARGS_KEY = 'handler_args'
MIME_OPML = 'text/x-opml+xml'
MIME_OCTET_STREAM = 'application/octet-stream'

lg = logging.getLogger()


def bot_handler(handler_cls, *args):
    args = list(args)
    def wrapper(method):
        setattr(method, HANDLER_CLS_KEY, handler_cls)
        setattr(method, HANDLER_ARGS_KEY, args)
        return method
    return wrapper


class BaseBot(object):
    def __init__(self, token):
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self.handlers = []

        # register commands
        for i in dir(self):
            method = getattr(self, i)
            if inspect.ismethod(method) and not i.startswith('_'):
                handler_cls = getattr(method, HANDLER_CLS_KEY, None)
                handler_args = getattr(method, HANDLER_ARGS_KEY, [])
                if handler_cls:
                    handler_args.append(method)
                    handler = handler_cls(*handler_args)
                    self.handlers.append(handler)
                    self.dispatcher.add_handler(handler)

    def run(self):
        print 'handlers:', self.handlers
        self.updater.start_polling()
        self.updater.idle()


class PodshareBot(BaseBot):
    help = """Hello there, this is Podshare bot, send me opml file to generate
a link to share your podcast subscriptions.
"""

    def init(self, file_dir):
        self.file_dir = file_dir

    @bot_handler(CommandHandler, 'start')
    def handle_start(self, bot, update):
        lg.info('cmd: start, update=%s', update)
        update.message.reply_text(text=self.help)

    @bot_handler(MessageHandler, ~Filters.command)
    def handle_message(self, bot, update):
        lg.info('msg: update=%s', update)
        doc = update.message.document
        if doc:
            if is_opml_doc(doc):
                self.process_document_opml(bot, update, doc)
            else:
                update.message.reply_text(text="wow a doc, it's {}".format(doc.mime_type))
        else:
            update.message.reply_text(text="send me opml pls")

    def process_document_opml(self, bot, update, doc):
        file = bot.get_file(doc.file_id)
        filename, _ = download_bot_file(file, 'opml', self.file_dir)
        update.message.reply_text(text="I've stored your opml file as {}, thanks".format(filename))


def download_bot_file(file, ext, file_dir):
    filename = '{}.{}'.format(file.file_id, ext)
    filepath = os.path.join(file_dir, filename)
    lg.info('downloading file: %s', filename)
    file.download(filepath)
    return filename, filepath


def is_opml_doc(doc):
    if doc.mime_type == MIME_OPML:
        return True
    if doc.mime_type == MIME_OCTET_STREAM and doc.file_name.endswith('.opml'):
        return True
    return False


def main():
    token = os.environ['BOT_TOKEN']
    file_dir = os.environ['BOT_FILE_DIR']
    bot = PodshareBot(token)
    bot.init(file_dir)
    bot.run()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG)
    main()
