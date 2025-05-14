import logging import base64 import aiohttp from aiogram import Bot, Dispatcher, types from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton from aiogram.utils import executor from aiogram.filters import CommandStart from PIL import Image, ImageDraw, ImageFont import os

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'

#Replace with your private channel IDs (must start with -100)

CHANNEL_IDS = [-1001234567890, -1009876543210] CHANNEL_LINKS = [ ('Channel 1', 'https://t.me/privatechannel1'), ('Channel 2', 'https://t.me/privatechannel2') ] ADMIN_ID = 7401896933 MAX_FREE_IMAGES = 2

bot = Bot(token=API_TOKEN) dp = Dispatcher(bot)

#In-memory user storage

user_images = {} user_referrals = {}

Inline buttons for channel join

join_keyboard = InlineKeyboardMarkup(inline_keyboard=[ [InlineKeyboardButton(text=name, url=link)] for name, link in CHANNEL_LINKS ])

#Check membership in all required channels

async def is_member(user_id): for channel_id in CHANNEL_IDS: try: member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id) if member.status not in ['member', 'administrator', 'creator']: return False except: return False return True

@dp.message(CommandStart()) async def start(message: types.Message): await message.answer( "\U0001F3A8 Ghibli Art Creation\n\nSend me a photo, and I'll transform it into a Ghibli-style masterpiece for you.\n\nUpload your photo below to start the transformation:")

@dp.message(lambda message: message.photo) async def handle_photo(message: types.Message): user_id = message.from_user.id

if not await is_member(user_id):
    await message.answer("\u274C You must join our channels to use this bot!", reply_markup=join_keyboard)
    return

count = user_images.get(user_id, 0) + user_referrals.get(user_id, 0)
if count >= MAX_FREE_IMAGES:
    await message.answer("\u26A0\uFE0F You've used your 2 free conversions. Refer friends to unlock more!\nEach referral = 1 more image.")
    return

# Download photo
file_info = await bot.get_file(message.photo[-1].file_id)
file_path = file_info.file_path
file_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"

async with aiohttp.ClientSession() as session:
    async with session.get(file_url) as resp:
        photo_data = await resp.read()

    # Send to external Ghibli API
    data = aiohttp.FormData()
    data.add_field('image', photo_data, filename='photo.jpg', content_type='image/jpeg')

    async with session.post('https://ghibli.kesug.com/?i=1', data=data) as api_resp:
        res = await api_resp.json()
        image_base64 = res.get('image_base64')
        if not image_base64:
            await message.answer("Something went wrong. Try again later.")
            return

        # Save image
        with open("ghibli_image.png", "wb") as f:
            f.write(base64.b64decode(image_base64))

# Add watermark
try:
    img = Image.open("ghibli_image.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 36) if os.path.exists("arial.ttf") else ImageFont.load_default()
    text = "@AryanXGhiblibot"
    text_width, text_height = draw.textsize(text, font=font)
    x = img.width - text_width - 10
    y = img.height - text_height - 10
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    img.save("ghibli_image.png")
except Exception as e:
    print("Watermarking failed:", e)

await message.answer_photo(photo=types.FSInputFile("ghibli_image.png"), caption="Here's your Ghibli-style art!")
user_images[user_id] = user_images.get(user_id, 0) + 1

@dp.message() async def referral_check(message: types.Message): if message.text.startswith('/ref '): try: ref_id = int(message.text.split()[1]) if ref_id != message.from_user.id: user_referrals[ref_id] = user_referrals.get(ref_id, 0) + 1 await bot.send_message(ref_id, f"\U0001F389 You received 1 extra Ghibli image credit! Total: {user_referrals[ref_id]}") await bot.send_message(ADMIN_ID, f"New user joined: @{message.from_user.username or message.from_user.first_name} (ID: {message.from_user.id})") except: pass

if name == 'main': logging.basicConfig(level=logging.INFO) executor.start_polling(dp, skip_updates=True)

