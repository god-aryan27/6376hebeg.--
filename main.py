import logging
import os
import base64
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from PIL import Image, ImageDraw, ImageFont

API_TOKEN = "7542705793:AAEKJhuZVXVvSli4t018aaTVVJISc73jNQA"  # replace with your bot token

# === Channel Setup ===
CHANNEL_IDS = [-1002316557460]  # replace with your private channel IDs
CHANNEL_LINKS = [
    ("Channel 1", "https://t.me/+o3dYShdRAZk4MWVl"),
    ("Channel 2", "https://t.me/yourchannel2")
]

# === Admin & Limits ===
ADMIN_ID = 7401896933
MAX_FREE_IMAGES = 2

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_images = {}       # Tracks number of images used by user
user_referrals = {}    # Tracks how many successful referrals user has

# === Inline Join Buttons ===
join_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text=name, url=url)] for name, url in CHANNEL_LINKS]
)

# === Channel Membership Checker ===
async def is_member(user_id):
    for channel_id in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# === Start Command ===
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    ref = message.get_args()
    if ref.isdigit():
        ref_id = int(ref)
        if ref_id != message.from_user.id:
            user_referrals[ref_id] = user_referrals.get(ref_id, 0) + 1
            await bot.send_message(ref_id, "🎉 You got +1 extra image! Thanks to your referral.")
            await bot.send_message(ADMIN_ID, f"New user joined via referral: {message.from_user.id}")

    # Referral Link
    bot_username = (await bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    referral_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Share Your Referral Link", url=referral_link)]
    ])

    await message.answer(
        "🎨 *Ghibli Art Creation*\n\nSend me a photo, and I'll transform it into a Ghibli-style masterpiece for you. ✨\n\nUpload your photo below to start:",
        parse_mode="Markdown",
        reply_markup=referral_keyboard
    )

# === Handle Photo Upload ===
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id

    if not await is_member(user_id):
        await message.answer("❌ You must join our channels to use this bot!", reply_markup=join_keyboard)
        return

    used = user_images.get(user_id, 0)
    bonus = user_referrals.get(user_id, 0)

    if used >= MAX_FREE_IMAGES + bonus:
        await message.answer("⛔ You’ve reached your limit! Invite friends to unlock more images.")
        return

    file = await bot.get_file(message.photo[-1].file_id)
    photo_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(photo_url) as resp:
            img_data = await resp.read()

        form = aiohttp.FormData()
        form.add_field("image", img_data, filename="photo.jpg", content_type="image/jpeg")

        async with session.post("https://ghibli.kesug.com/?i=1", data=form) as api_resp:
            res = await api_resp.json()
            base64_img = res.get("image_base64")

            if not base64_img:
                await message.answer("❌ Failed to generate image. Try again later.")
                return

            with open("ghibli.png", "wb") as f:
                f.write(base64.b64decode(base64_img))

    # === Add Watermark ===
    try:
        img = Image.open("ghibli.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 36) if os.path.exists("arial.ttf") else ImageFont.load_default()
        text = "@AryanXGhiblibot"
        text_width, text_height = draw.textsize(text, font=font)
        x = img.width - text_width - 20
        y = img.height - text_height - 20
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        img.save("ghibli.png")
    except Exception as e:
        print(f"Watermark error: {e}")

    user_images[user_id] = used + 1
    await message.answer_photo(types.FSInputFile("ghibli.png"), caption="Here’s your Ghibli-style art!")

# === Launch Bot ===
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
