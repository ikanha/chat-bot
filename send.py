from telegram import Bot
import asyncio
from dotenv import load_dotenv
load_dotenv()
import os
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = 1775108698
bot = Bot(token=BOT_TOKEN)

async def send_message(text):

    bot = Bot(token=BOT_TOKEN)

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )


# while True:
#     text = input("enter message to send: ")
#     if text == "quit":
#         break
#     else:
#         asyncio.run(send_message(text))


#send photos
async def send_photo():

    bot = Bot(token=BOT_TOKEN)

    with open("downloads/3d15a713-97f6-4df2-9fa4-838aea971924.jpg", "rb") as photo:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=photo,
            caption="Hello Kanhaiya! 📸"
        )


async def send_video():

    bot = Bot(token=BOT_TOKEN)

    with open("video.mp4", "rb") as video:
        await bot.send_video(
            chat_id=CHAT_ID,
            video=video,
            caption="Here is your video 🎥"
        )


async def send_audio():

    bot = Bot(token=BOT_TOKEN)

    with open("audio.mp3", "rb") as audio:
        await bot.send_audio(
            chat_id=CHAT_ID,
            audio=audio,
            caption="Here is your audio 🔊"
        )





async def send_file(chat_id, file_path):

    ext = file_path.split(".")[-1].lower()

    with open(file_path, "rb") as f:

        if ext in ["jpg", "jpeg", "png"]:
            await bot.send_photo(chat_id=chat_id, photo=f)

        elif ext in ["mp4", "mov", "avi"]:
            await bot.send_video(chat_id=chat_id, video=f)

        elif ext in ["mp3", "wav", "ogg"]:
            await bot.send_audio(chat_id=chat_id, audio=f)

        else:
            await bot.send_document(chat_id=chat_id, document=f)

asyncio.run(send_file(CHAT_ID,r'downloads/b161a045-2863-44dc-b6f6-527a88421da0.jpg'))