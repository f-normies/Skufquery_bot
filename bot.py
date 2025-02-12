import os
import json
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, PollAnswerHandler

from polls import new_poll, receive_poll_answer, close_poll, list_polls
from all import tag_all

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
approved_users = json.loads(os.getenv('ADMINS'))
chat_id = os.getenv('chat_id')
message_thread_id = os.getenv('message_thread_id')

polls_filename = "./polls_data.json"
tmp_folder = "./tmp"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)

if not os.path.exists(polls_filename):
    with open(polls_filename, 'w') as file:
        json.dump({}, file)

with open(polls_filename, 'r') as file:
    polls_data = json.load(file)

def save_polls_data():
    with open(polls_filename, 'w') as file:
        json.dump(polls_data, file, indent=4)

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    new_poll_handler = CommandHandler('new', lambda update, context: new_poll(update, context, polls_data, save_polls_data, logger))
    poll_answer_handler = PollAnswerHandler(lambda update, context: receive_poll_answer(update, context, polls_data, save_polls_data, logger))
    close_poll_handler = CommandHandler('close', lambda update, context: close_poll(update, context, polls_data, save_polls_data, logger))
    list_polls_handler = CommandHandler('polls', lambda update, context: list_polls(update, context, polls_data, logger))
    all_handler = CommandHandler('all', lambda update, context: tag_all(update, context, API_ID, API_HASH, TOKEN, logger))
    
    application.add_handler(new_poll_handler)
    application.add_handler(poll_answer_handler)
    application.add_handler(close_poll_handler)
    application.add_handler(list_polls_handler)
    application.add_handler(all_handler)

    application.run_polling()
