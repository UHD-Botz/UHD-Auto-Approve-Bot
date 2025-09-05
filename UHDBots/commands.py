import random
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import *
from config import *
from Script import text
from .db import tb

# ================== FORCE SUB ================== #
async def get_fsub(client, message):
    try:
        member = await client.get_chat_member(FSUB_CHANNEL, message.from_user.id)
        if member.status in [enums.ChatMemberStatus.BANNED]:
            await message.reply("🚫 You are banned from using this bot.")
            return False
    except:
        invite = await client.create_chat_invite_link(FSUB_CHANNEL)
        await message.reply(
            "⚠️ You must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join Channel", url=invite.invite_link)]]
            )
        )
        return False
    return True

# ================== START ================== #
@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    if await tb.get_user(message.from_user.id) is None:
        await tb.add_user(message.from_user.id, message.from_user.first_name)
        bot = await client.get_me()
        await client.send_message(
            LOG_CHANNEL,
            text.LOG.format(
                message.from_user.id,
                getattr(message.from_user, "dc_id", "N/A"),
                message.from_user.first_name or "N/A",
                f"@{message.from_user.username}" if message.from_user.username else "N/A",
                bot.username
            )
        )
    if IS_FSUB and not await get_fsub(client, message): return
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=text.START.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('⇆ Add Me To Your Group ⇆', url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ℹ️ About', callback_data='about'),
             InlineKeyboardButton('📚 Help', callback_data='help')],
            [InlineKeyboardButton('⇆ Add Me To Your Channel ⇆', url=f"https://t.me/{BOT_USERNAME}?startchannel=true&admin=invite_users")]
        ])
    )

# ================== HELP ================== #
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    reply = await message.reply(
        text=("❓ <b>Having Trouble?</b>\n\nWatch the tutorial below."),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Watch Tutorial", url="https://youtu.be/_n3V0gFZMh8")]
        ])
    )
    await asyncio.sleep(300)
    await reply.delete()
    try:
        await message.delete()
    except:
        pass

# ================== ACCEPT ================== #
@Client.on_message(filters.command('accept') & filters.private)
async def accept(client, message):
    show = await message.reply("**Please Wait.....**")
    user_data = await tb.get_session(message.from_user.id)
    if user_data is None:
        return await show.edit("**To accept join requests, please /login first.**")
    try:
        acc = Client("joinrequest", session_string=user_data, api_id=API_ID, api_hash=API_HASH)
        await acc.connect()
    except:
        return await show.edit("**Your login session has expired. Use /logout first, then /login again.**")
    await show.edit("**Forward a message from your Channel or Group.**")
    fwd_msg = await client.listen(message.chat.id)
    if fwd_msg.forward_from_chat and fwd_msg.forward_from_chat.type not in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
        chat_id = fwd_msg.forward_from_chat.id
        try:
            info = await acc.get_chat(chat_id)
        except:
            return await show.edit("**Error: Ensure your account is admin.**")
    else:
        return await message.reply("**Invalid forward.**")
    await fwd_msg.delete()
    msg = await show.edit("**Accepting all join requests...**")
    try:
        while True:
            await acc.approve_all_chat_join_requests(chat_id)
            await asyncio.sleep(1)
            join_requests = [req async for req in acc.get_chat_join_requests(chat_id)]
            if not join_requests:
                break
        await msg.edit("**✅ Successfully accepted all join requests.**")
    except Exception as e:
        await msg.edit(f"**Error:** `{str(e)}`")

# ================== AUTO APPROVE NEW ================== #
@Client.on_chat_join_request()
async def approve_new(client, m):
    if not NEW_REQ_MODE:
        return
    try:
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        try:
            await client.send_message(
                m.from_user.id,
                f"{m.from_user.mention},\n\nYour Request To Join {m.chat.title} Has Been Accepted ✅"
            )
        except:
            pass
    except Exception as e:
        print(str(e))
        pass

# ================== ADMIN (BAN / UNBAN) ================== #
@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a user to ban.")
    user_id = message.reply_to_message.from_user.id
    await tb.ban_user(user_id)
    await message.reply(f"🚫 User {user_id} banned.")

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a user to unban.")
    user_id = message.reply_to_message.from_user.id
    await tb.unban_user(user_id)
    await message.reply(f"✅ User {user_id} unbanned.")

# ================== BROADCAST ================== #
@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_cmd(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")
    users = await tb.get_all_users()
    success = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            success += 1
        except:
            pass
    await message.reply(f"✅ Broadcasted to {success} users.")

# ================== CALLBACK ================== #
@Client.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    if query.data == "about":
        await query.message.edit_caption(
            "🤖 This is an Auto-Approve Bot.\n\nMade with ❤️ by UHD Bots",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
            )
        )
    elif query.data == "help":
        await query.message.edit_caption(
            "📚 Help Section:\n\nUse /accept to approve join requests.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
            )
        )
    elif query.data == "home":
        await query.message.edit_caption(
            text.START.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⇆ Add Me To Your Group ⇆', url=f"https://t.me/{BOT_USERNAME}?startgroup=true&admin=invite_users")],
                [InlineKeyboardButton('ℹ️ About', callback_data='about'),
                 InlineKeyboardButton('📚 Help', callback_data='help')]
            ])
        )

# ================== MAINTENANCE MODE ================== #
@Client.on_message(filters.command("maintenance") & filters.user(ADMINS))
async def maintenance_toggle(client, message: Message):
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = not MAINTENANCE_MODE
    status = "ON 🔴" if MAINTENANCE_MODE else "OFF 🟢"
    await message.reply(f"⚙️ Maintenance Mode {status}")
