import logging
import base64
import aiohttp
import os
import asyncio
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties
from aiogram import F
from aiogram import Router
from aiogram.fsm.storage.memory import MemoryStorage

# CONFIG
BOT_TOKEN = "7542705793:AAEKJhuZVXVvSli4t018aaTVVJISc73jNQA"
ADMIN_ID = 7401896933
CHANNEL_IDS = [-1002316557460]
CHANNEL_LINKS = [
    ("Channel 1", "https://t.me/+o3dYShdRAZk4MWVl")
]
MAX_FREE_IMAGES = 2

# LOGGING
logging.basicConfig(level=logging.INFO)

# MEMORY
user_data = {}

# INIT BOT & DISPATCHER
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Check user joined
async def is_user_joined(user_id):
    for channel_id in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

# Generate image
async def generate_ghibli_image(photo_path):
    url = "https://ghibli.kesug.com/"
    with open(photo_path, "rb") as f:
        photo_bytes = f.read()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={"file": photo_bytes}) as resp:
            data = await resp.json()
            base64_image = data["image_base64"]
            output_path = "ghibli_output.png"
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(base64_image))
            # Watermark
            img = Image.open(output_path)
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 36) if os.path.exists("arial.ttf") else ImageFont.load_default()
            draw.text((img.width - 300, img.height - 50), "@AryanXGhiblibot", (255, 255, 255), font=font)
            img.save(output_path)
            return output_path

@router.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"used": 0, "referrals": 0}
        await bot.send_message(ADMIN_ID, f"New user joined: {message.from_user.full_name} ({user_id})")

    await message.answer(
        "🎨 <b>Ghibli Art Generator</b>\n\n"
        "Send me a photo and I’ll convert it to beautiful Ghibli-style art!"
    )

@router.message(F.text.startswith("/start "))
async def referral_handler(message: types.Message):
    try:
        referrer_id = int(message.text.split(" ")[1])
        user_id = message.from_user.id
        if user_id != referrer_id and user_id not in user_data:
            user_data[user_id] = {"used": 0, "referrals": 0}
            if referrer_id in user_data:
                user_data[referrer_id]["referrals"] += 1
                await bot.send_message(referrer_id, f"✅ You got a referral! You now have {user_data[referrer_id]['referrals']} extra image(s).")
            await bot.send_message(ADMIN_ID, f"New user joined via referral: {user_id} by {referrer_id}")
    except:
        pass
    await start(message)

@router.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if not await is_user_joined(user_id):
        buttons = [[InlineKeyboardButton(text=name, url=link)] for name, link in CHANNEL_LINKS]
        await message.answer("❌ Please join our channels first to continue.", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    if user_data[user_id]["used"] >= (MAX_FREE_IMAGES + user_data[user_id]["referrals"]):
        await message.answer(
            "You've used all your free image generations.\n"
            f"Invite others to get more:\nhttps://t.me/{(await bot.get_me()).username}?start={user_id}"
        )
        return

    await message.answer("⏳ Processing your image (0%)...")
    await asyncio.sleep(1)
    await message.answer("⏳ Processing your image (30%)...")
    await asyncio.sleep(1)
    await message.answer("⏳ Processing your image (70%)...")
    await asyncio.sleep(1)

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_path = "input.jpg"
    await bot.download_file(file.file_path, photo_path)

    try:
        output_path = await generate_ghibli_image(photo_path)
        await message.answer_photo(types.FSInputFile(output_path), caption="Here's your Ghibli-style art!")
        user_data[user_id]["used"] += 1
    except Exception as e:
        await message.answer("❌ Failed to generate image.")
        print("Error:", e)

# Start polling
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
