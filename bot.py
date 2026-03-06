import os
import asyncio
import base64
import pdfplumber
import cv2

from dotenv import load_dotenv
from colorama import Fore, init

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

from telegram.constants import ChatAction
from langchain_core.messages import HumanMessage

from graph import app

from PIL import Image
import pytesseract


init()
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

MAX_LENGTH = 4096

os.makedirs("downloads", exist_ok=True)
os.makedirs("frames", exist_ok=True)


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Hello! I am your AI assistant 🤖"
    )


# TYPING INDICATOR
async def typing_indicator(context, chat_id):

    while True:

        await context.bot.send_chat_action(
            chat_id,
            ChatAction.TYPING
        )

        await asyncio.sleep(4)


# SPLIT LONG MESSAGE
def split_message(text, size=4096):

    return [
        text[i:i+size]
        for i in range(0, len(text), size)
    ]


# IMAGE → BASE64
def image_to_base64(path):

    with open(path, "rb") as f:

        return base64.b64encode(
            f.read()
        ).decode()


# VIDEO FRAME EXTRACTION (OpenCV)
def extract_frame(video_path):

    frame_path = "frames/frame.jpg"

    cap = cv2.VideoCapture(video_path)

    success, frame = cap.read()

    if success:

        cv2.imwrite(frame_path, frame)

    cap.release()

    return frame_path


# READ PDF
def read_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:

            text += page.extract_text() or ""

    return text[:5000]


# OCR IMAGE
def ocr_image(path):

    img = Image.open(path)

    return pytesseract.image_to_string(img)


# MAIN MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        message = update.message

        first_name = update.effective_user.first_name

        user_id = str(update.effective_user.id)

        chat_id = update.effective_chat.id
        print(f'effective_chat : {update}')

        print(f"chat id is {chat_id}")

        human_message = None


        # TEXT MESSAGE
        if message.text:

            print(Fore.RED + f"{first_name}: {message.text}")

            human_message = HumanMessage(
                content=message.text
            )


        # IMAGE
        elif message.photo:

            photo = message.photo[-1]

            file = await photo.get_file()

            path = f"downloads/{photo.file_id}.jpg"

            await file.download_to_drive(path)

            base64_img = image_to_base64(path)

            user_text = message.caption or "User sent an image"

            human_message = HumanMessage(
                content=[
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        },
                    },
                ]
            )


        # VIDEO
        elif message.video:

            video = message.video

            file = await video.get_file()

            path = f"downloads/{video.file_id}.mp4"

            await file.download_to_drive(path)

            frame = extract_frame(path)

            base64_img = image_to_base64(frame)

            user_text = message.caption or "User sent a video"

            human_message = HumanMessage(
                content=[
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        },
                    },
                ]
            )


        # DOCUMENT
        elif message.document:

            doc = message.document

            file = await doc.get_file()

            path = f"downloads/{doc.file_name}"

            await file.download_to_drive(path)

            user_text = message.caption or "User uploaded a document"

            if path.endswith(".pdf"):

                text = read_pdf(path)

            else:

                with open(path, "r", errors="ignore") as f:

                    text = f.read()

            human_message = HumanMessage(
                content=f"{user_text}\n\nDocument Content:\n{text}"
            )


        # AUDIO / VOICE
        elif message.voice or message.audio:

            audio = message.voice or message.audio

            file = await audio.get_file()

            path = f"downloads/{audio.file_id}.ogg"

            await file.download_to_drive(path)

            user_text = message.caption or "User sent an audio message"

            human_message = HumanMessage(
                content=user_text
            )


        else:

            await update.message.reply_text(
                "Unsupported message type."
            )

            return


        typing_task = asyncio.create_task(
            typing_indicator(context, chat_id)
        )

        sent_msg = await update.message.reply_text(
            "Thinking..."
        )

        reply = ""


        stream = app.stream(
            {"messages": [human_message],
             "user_phone": 'phone'},
            {"configurable": {"thread_id": user_id}},
        )


        for chunk in stream:

            if "chatbot" in chunk:

                messages = chunk["chatbot"]["messages"]

                if messages:

                    reply = messages[-1].content

                    if isinstance(reply, list):

                        reply = str(reply)

                    if len(reply) <= MAX_LENGTH:

                        await sent_msg.edit_text(reply)

                    else:

                        parts = split_message(reply)

                        await sent_msg.edit_text(parts[0])

                        for part in parts[1:]:

                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=part
                            )


        typing_task.cancel()

        print(Fore.GREEN + f"Reply: {reply}")


    except Exception as e:

        print("Error:", e)

        await update.message.reply_text(
            "Something went wrong."
        )


# MAIN
def main():

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT
            | filters.PHOTO
            | filters.VIDEO
            | filters.Document.ALL
            | filters.VOICE
            | filters.AUDIO,
            handle_message,
        )
    )

    print("Telegram bot running...")

    application.run_polling()


if __name__ == "__main__":

    main()