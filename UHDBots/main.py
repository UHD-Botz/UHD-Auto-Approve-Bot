import traceback
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import *
from .db import tb

SESSION_STRING_SIZE = 351

# -------------------- LOGOUT -------------------- #
@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    user_id = message.from_user.id
    session = await tb.get_session(user_id)
    if session is None:
        return
    await tb.set_session(user_id, session=None)
    await message.reply("**✅ Logout Successfully** ♦")

# -------------------- LOGIN -------------------- #
@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    # ✅ Maintenance check moved here
    from .commands import MAINTENANCE_MODE  

    if MAINTENANCE_MODE and message.from_user.id != ADMIN:
        await message.delete()
        return await message.reply_text(
            "**🛠️ Bot is Under Maintenance**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Support", user_id=int(ADMIN))]]
            )
        )

    user_id = message.from_user.id
    session = await tb.get_session(user_id)
    if session is not None:
        await message.reply("**You are already logged in. Please /logout first before logging in again.**")
        return

    phone_number_msg = await bot.ask(
        chat_id=user_id,
        text="<b>Pl
