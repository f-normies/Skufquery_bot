import os
import subprocess
from telegram import Update
from telegram.ext import ContextTypes
import logging

async def lecture(update: Update, context: ContextTypes.DEFAULT_TYPE, approved_users, tmp_folder, chat_id, message_thread_id, logger) -> None:
    user_id = update.message.from_user.id

    if user_id not in approved_users:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Вы не авторизованы для использования этой команды.")
        return

    if not context.args or not update.message.document:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Использование: /lecture <заголовок> <вложенный mp4 файл>")
        return

    heading = " ".join(context.args)
    file = update.message.document

    if file.mime_type != "video/mp4":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Пожалуйста, прикрепите файл в формате mp4.")
        return

    try:
        logger.info(f"Downloading video for user {user_id} to {input_video}")
        file_path = await context.bot.get_file(file.file_id)
        await file_path.download_to_drive(input_video)
    except Exception as e:
        logger.error(f"Error downloading file for user {user_id}: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Ошибка при загрузке файла.")
        return

    file_path = await context.bot.get_file(file.file_id)
    await file_path.download_to_drive(input_video)

    command = [
        "cvlc", "-I", "dummy", input_video,
        "--sout", f"#transcode{{vcodec=h264,acodec=mp3,vb=800,ab=128}}:standard{{mux=mp4,dst={output_video},access=file}}", 
        "vlc://quit"
    ]
    
    logger.info(f"Running VLC command: {command}")
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        with open(output_video, "rb") as video:
            await context.bot.send_document(chat_id=chat_id,
                                            message_thread_id=message_thread_id, 
                                            document=video, 
                                            caption=heading)

        os.remove(input_video)
        os.remove(output_video)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Видео успешно отправлено.")
    else:
        logger.error(f"Error during video compression for {input_video}: {process.stderr.decode()}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Ошибка при сжатии видео.")