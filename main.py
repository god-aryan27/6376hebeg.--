import logging import base64 import aiohttp import asyncio import os from aiogram import Bot, Dispatcher, types from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton from aiogram.utils import executor from aiogram.filters import CommandStart from PIL import Image, ImageDraw, ImageFont

API_TOKEN = '7542705793:AAEKJhuZVXVvSli4t018aaTVVJISc73jNQA' CHANNEL_IDS = [-1002316557460]  # Your private channel IDs 
CHANNEL_LINKS = [ ('Channel 1', 'https://t.me/+o3dYShdRAZk4MWVl'), ('Channel 2', 'https://t.me/privatechannel2') ] 
ADMIN_ID = 7401896933 
MAX_FREE_IMAGES = 2

bot = Bot(token=API_TOKEN) dp = Dispatcher()

user_limits = {} user_refs = {}

@dp.message(CommandStart()) async def start_cmd(message: types.Message): user_id = message.from_user.id if user_id not in user_limits: user_limits[user_id] = 0 await bot.send_message(ADMIN_ID, f"New user joined: {message.from_user.full_name} ({user_id})")

await message.answer(
    "🎨 Ghibli Art Creation\n\nSend me a photo, and I'll transform it into a Ghibli-style masterpiece for you. ✨\n\nUpload your photo below to start the transformation:")

@dp.message(lambda msg: msg.photo) async def handle_photo(message: types.Message): user_id = message.from_user.id

# Check channel membership
for channel_id in CHANNEL_IDS:
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        if member.status in ['left', 'kicked']:
            raise Exception("Not a member")
    except:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=name, url=link)] for name, link in CHANNEL_LINKS]
        )
        return await message.answer("❌ You must join our channels to use this bot!\n\n🔔 Click the buttons below to join, then try again.", reply_markup=kb)

# Check usage limit
if user_limits.get(user_id, 0) >= MAX_FREE_IMAGES + user_refs.get(user_id, 0):
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    return await message.answer(f"You've reached your image limit. Refer friends to get more!\n\nYour referral link:\n{ref_link}")

await message.answer("Processing... 0%")
await asyncio.sleep(0.5)
await message.answer("Processing... 30%")
await asyncio.sleep(0.5)
await message.answer("Processing... 70%")
await asyncio.sleep(0.5)
await message.answer("Processing... 100%")

photo = message.photo[-1]
photo_file = await bot.get_file(photo.file_id)
photo_path = await bot.download_file(photo_file.file_path)

with open(f"input_{user_id}.jpg", "wb") as f:
    f.write(photo_path.read())

async with aiohttp.ClientSession() as session:
    with open(f"input_{user_id}.jpg", 'rb') as img_file:
        encoded = base64.b64encode(img_file.read()).decode('utf-8')
    payload = {'image_base64': encoded}
    async with session.post('https://ghibli.kesug.com/', json=payload) as resp:
        res = await resp.json()

decoded_image = base64.b64decode(res['image_base64'])
output_path = f"ghibli_{user_id}.png"
with open(output_path, "wb") as f:
    f.write(decoded_image)

# Add watermark
img = Image.open(output_path)
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("arial.ttf", 36) if os.path.exists("arial.ttf") else ImageFont.load_default()
draw.text((img.width - 300, img.height - 50), "@AryanXGhiblibot", font=font, fill="white")
img.save(output_path)

await message.answer_photo(types.FSInputFile(output_path), caption="Here's your Ghibli-style art!")
user_limits[user_id] += 1

@dp.message(lambda msg: msg.text and msg.text.startswith("/start ")) async def referral_start(message: types.Message): ref_id = int(message.text.split()[1]) user_id = message.from_user.id if ref_id != user_id: user_refs[ref_id] = user_refs.get(ref_id, 0) + 1 await bot.send_message(ref_id, f"You've got a new referral! You've earned 1 extra image.") await start_cmd(message)

if name == 'main': logging.basicConfig(level=logging.INFO) executor.start_polling(dp, skip_updates=True)

