import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from telethon import TelegramClient

async def get_users(client, group_id):
    users = []
    async for user in client.iter_participants(group_id):
        if not user.deleted:
            users.append(user)
    return users

async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE, API_ID, API_HASH, TOKEN, logger) -> None:
    client = None
    try:
        client = TelegramClient('bot', API_ID, API_HASH)
        await client.start(bot_token=TOKEN)
        
        chat_id = update.effective_chat.id
        
        users = await get_users(client, chat_id)
        
        mentions = []
        bot_user = await context.bot.get_me()
        
        for user in users:
            if user.id != bot_user.id:  # Исключаем бота
                mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                mentions.append(mention)
        
        if mentions:
            message_text = ', '.join(mentions)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text=message_text,
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text="В группе нет участников для тегирования."
            )
            
    except BadRequest as e:
        logger.error(f"Failed to tag all users: {e.message}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text="Не удалось отметить всех пользователей."
        )
    finally:
        if client:
            await client.disconnect()
