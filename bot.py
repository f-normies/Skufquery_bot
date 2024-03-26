from telegram import *
from telegram.ext import *
from telegram.error import BadRequest
import asyncio
import logging
import random
from random import randint
import json
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = 'здесь должен быть ваш токен'
polls_filename = "./polls_data.json"

if not os.path.exists(polls_filename):
    with open(polls_filename, 'w') as file:
        json.dump({}, file)

with open(polls_filename, 'r') as file:
        polls_data = json.load(file)

def save_polls_data():
    with open(polls_filename, 'w') as file:
        json.dump(polls_data, file, indent=4)

async def new_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       reply_to_message_id=update.message.message_id,
                                       text="Использование: /new <название опроса>")
        return

    poll_id = randint(1000, 9999)
    while str(poll_id) in polls_data:
        poll_id = randint(1000, 9999)

    question = " ".join(context.args) + f" ({poll_id})"
    options = ["Да", "Да (с приоритетом)", "Нет"]

    message = await context.bot.send_poll(chat_id=update.effective_chat.id,
                                          reply_to_message_id=update.message.message_id,
                                          question=question,
                                          options=options,
                                          is_anonymous=False,
                                          allows_multiple_answers=False)

    telegram_poll_id = message.poll.id

    polls_data[str(poll_id)] = {
        'telegram_poll_id': telegram_poll_id,
        'message_id': message.message_id,
        'chat_id': update.effective_chat.id,
        'poll_title': " ".join(context.args),
        'priority_users': [],
        'normal_users': [],
        'no_users': []
    }

    save_polls_data()

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Received poll answer")
    telegram_poll_id = update.poll_answer.poll_id
    user_id = update.poll_answer.user.id
    option_ids = update.poll_answer.option_ids

    custom_poll_id = None
    for pid, info in polls_data.items():
        if info['telegram_poll_id'] == telegram_poll_id:
            custom_poll_id = pid
            break

    if custom_poll_id is None:
        logger.error(f"Опроса с Telegram ID {telegram_poll_id} не существует.")
        return

    poll_info = polls_data[custom_poll_id]

    if not option_ids:
        for queue_type in ['priority_users', 'normal_users', 'no_users']:
            if user_id in poll_info.get(queue_type, []):
                poll_info[queue_type].remove(user_id)
                logger.info(f"User {user_id} removed from {queue_type}")
    else:
        option_id = option_ids[0]
        queue_type = 'priority_users' if option_id == 1 else 'normal_users' if option_id == 0 else 'no_users'

        if user_id not in poll_info.get(queue_type, []):
            poll_info[queue_type].append(user_id)
            logger.info(f"User {user_id} added to {queue_type}")

    save_polls_data()

async def close_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    force_close = False
    poll_id_arg = None

    if '-f' in context.args:
        force_close = True
        context.args.remove('-f')
    
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       reply_to_message_id=update.message.message_id,
                                       text="Использование: /close [-f] <4-значный ID>. Пояснение -- аргумент \"-f\" отвечает за принудительное закрытие и удаление опроса.")
        return

    try:
        custom_poll_id = context.args[0]
        if custom_poll_id not in polls_data:
            await context.bot.send_message(chat_id=update.effective_chat.id, 
                                           reply_to_message_id=update.message.message_id, 
                                           text="Опроса с таким ID не существует.")
            return
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       reply_to_message_id=update.message.message_id,
                                       text="Неверный формат ID опроса.")
        return

    poll_info = polls_data[custom_poll_id]
    chat_id = poll_info['chat_id']
    message_id = poll_info['message_id']

    try:
        await context.bot.stop_poll(chat_id=chat_id, message_id=message_id)
    except BadRequest as e:
        logger.error(f"Failed to stop the poll: {e.message}")
        if force_close:
            del polls_data[custom_poll_id]
            save_polls_data()
            await context.bot.send_message(chat_id=chat_id, 
                                           reply_to_message_id=update.message.message_id, 
                                           text="Опрос принудительно закрыт и удален.")
            return
        else:
            await context.bot.send_message(chat_id=chat_id, 
                                           reply_to_message_id=update.message.message_id, 
                                           text="Не удалось остановить опрос. Используйте аргумент \"-f\" для принудительного закрытия.")
            return

    priority_users = poll_info.get('priority_users', [])
    normal_users = poll_info.get('normal_users', [])
    no_users = poll_info.get('no_users', [])
    seed = random.randint(0, 99999)
    random.seed(seed)
    random.shuffle(priority_users)
    random.shuffle(normal_users)

    combined_queue = priority_users + normal_users

    queue_message = "Очередь:\n"
    for i, user_id in enumerate(combined_queue, start=1):
        user = await context.bot.get_chat(user_id)
        queue_message += f"{i}. {user.first_name}\n"
        
    if no_users:
        queue_message += "\nОтказались:\n"
        for i, user_id in enumerate(no_users, start=1):
            user = await context.bot.get_chat(user_id)
            queue_message += f"{i}. {user.first_name}\n"

    queue_message += f"\nСлучайный seed: {seed}"

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   reply_to_message_id=update.message.message_id,
                                   text=queue_message)

    del polls_data[custom_poll_id]
    save_polls_data()

async def list_polls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not polls_data:
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       reply_to_message_id=update.message.message_id, 
                                       text="Нет активных опросов.")
        return
    
    polls_list_message = "Активные опросы:\n"
    for poll_id, poll_info in polls_data.items():
        poll_title = poll_info.get('poll_title', 'Нет названия')
        polls_list_message += f"ID: {poll_id} - Название: {poll_title}\n"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   reply_to_message_id=update.message.message_id,
                                   text=polls_list_message)

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    new_poll_handler = CommandHandler('new', new_poll)
    poll_answer_handler = PollAnswerHandler(receive_poll_answer)
    close_poll_handler = CommandHandler('close', close_poll)
    list_polls_handler = CommandHandler('polls', list_polls)

    application.add_handler(new_poll_handler)
    application.add_handler(poll_answer_handler)
    application.add_handler(close_poll_handler)
    application.add_handler(list_polls_handler)

    application.run_polling()