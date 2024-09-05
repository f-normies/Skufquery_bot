import os
import json
import logging
from telegram.ext import Application, CommandHandler, PollAnswerHandler

from polls import new_poll, receive_poll_answer, close_poll, list_polls
from lecture import lecture

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TOKEN = 'здесь должен быть ваш токен'
polls_filename = "./polls_data.json"

approved_users = [722943695]
tmp_folder = "./tmp"
# КАНАЛ ЛЕКЦИЙ:
# chat_id = -1002146633238
# message_thread_id = 30929

# ТЕСТОВЫЙ КАНАЛ:
chat_id = -1002160467382
message_thread_id = 4

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
    lecture_handler = CommandHandler('lecture', lambda update, context: lecture(update, context, approved_users, tmp_folder, chat_id, message_thread_id, logger))

    application.add_handler(new_poll_handler)
    application.add_handler(poll_answer_handler)
    application.add_handler(close_poll_handler)
    application.add_handler(list_polls_handler)
    application.add_handler(lecture_handler)

    application.run_polling()
