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
from .commands import get_maintenance   # you merged maintenance.py into commands.py

SESSION_STRING_SIZE = 351


@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message: Message):
    user_id = message.from_user.id
    session = await tb.get_session(user_id)
    if session is None:
        return await message.reply("**You are not logged in.**")
    await tb.set_session(user_id, session=None)
    await message.reply("**✅ Logout Successfully**")


@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    if await get_maintenance() and message.from_user.id != ADMIN:
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
        return await message.reply(
            "**⚠️ You are already logged in.\nUse /logout first before logging in again.**"
        )

    # Step 1: Ask for phone number
    phone_number_msg = await bot.ask(
        chat_id=user_id,
        text=(
            "<b>Please send your phone number which includes country code.</b>\n\n"
            "<b>Example:</b>\n"
            "<code>+13124562345</code>\n"
            "<code>+9171828181889</code>\n\n"
            "Send <code>/cancel</code> to stop the process."
        )
    )
    if phone_number_msg.text == "/cancel":
        return await phone_number_msg.reply("<b>❌ Process cancelled!</b>")

    phone_number = phone_number_msg.text
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    await phone_number_msg.reply("📩 Sending OTP...")

    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(
            user_id,
            (
                "Check your official Telegram account for OTP.\n\n"
                "If you got it, send it here as shown:\n\n"
                "👉 If OTP is `12345`, send it as: `1 2 3 4 5`\n\n"
                "Send <code>/cancel</code> to stop."
            ),
            filters=filters.text,
            timeout=600
        )
    except PhoneNumberInvalid:
        return await phone_number_msg.reply("❌ <b>Invalid phone number.</b>")

    if phone_code_msg.text == "/cancel":
        return await phone_code_msg.reply("<b>❌ Process cancelled!</b>")

    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        return await phone_code_msg.reply("❌ <b>Invalid OTP provided.</b>")
    except PhoneCodeExpired:
        return await phone_code_msg.reply("⏰ <b>OTP expired.</b>")
    except SessionPasswordNeeded:
        two_step_msg = await bot.ask(
            user_id,
            (
                "🔑 Two-step verification is enabled.\n\n"
                "Please send your password.\n\n"
                "Send <code>/cancel</code> to stop."
            ),
            filters=filters.text,
            timeout=300
        )
        if two_step_msg.text == "/cancel":
            return await two_step_msg.reply("<b>❌ Process cancelled!</b>")
        try:
            await client.check_password(password=two_step_msg.text)
        except PasswordHashInvalid:
            return await two_step_msg.reply("❌ <b>Invalid password provided.</b>")

    string_session = await client.export_session_string()
    await client.disconnect()

    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply("<b>❌ Invalid session string.</b>")

    try:
        await tb.set_session(user_id, string_session)
    except Exception as e:
        return await message.reply_text(f"<b>⚠️ ERROR IN LOGIN:</b> `{e}`")

    await bot.send_message(
        user_id,
        (
            "<b>✅ Account logged in successfully.</b>\n\n"
            "If you get any <code>AUTH KEY</code> related error, use /logout and /login again."
        )
    )
