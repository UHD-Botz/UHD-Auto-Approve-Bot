import os
from datetime import datetime
from pytz import timezone
from pyrogram import Client
from aiohttp import web
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN, LOG_CHANNEL

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route(request):
    return web.Response(
        text="<h3 align='center'><b>I am Alive 🚀</b></h3>", 
        content_type='text/html'
    )

async def web_server():
    app = web.Application(client_max_size=30_000_000)
    app.add_routes(routes)
    return app

class Bot(Client):
    def __init__(self):
        super().__init__(
            "UHD-Auto-Approve-Bot",   # session name updated
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="UHDBots"),  # make sure your plugins folder = plugins/
            workers=200,
            sleep_threshold=15
        )
        self.me = None  # store bot info globally

    async def start(self):
        # Start web server
        try:
            runner = web.AppRunner(await web_server())
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
            await site.start()
            print("✅ Web server started.")
        except Exception as e:
            print(f"❌ Web server error: {e}")

        # Start bot
        await super().start()
        self.me = await self.get_me()
        print(f"🤖 Bot started as {self.me.first_name}")

        # Notify ADMIN
        try:
            admin_id = int(ADMIN) if ADMIN else None
            if admin_id:
                await self.send_message(admin_id, f"✅ **{self.me.first_name} is now online...**")
        except Exception as e:
            print(f"⚠️ Error sending message to ADMIN: {e}")

        # Log to channel
        if LOG_CHANNEL:
            try:
                now = datetime.now(timezone("Asia/Kolkata"))
                msg = (
                    f"**{self.me.mention} restarted successfully!**\n\n"
                    f"📅 Date : `{now.strftime('%d %B, %Y')}`\n"
                    f"⏰ Time : `{now.strftime('%I:%M:%S %p')}`\n"
                    f"🌐 Timezone : `Asia/Kolkata`"
                )
                await self.send_message(LOG_CHANNEL, msg)
            except Exception as e:
                print(f"⚠️ Error sending to LOG_CHANNEL: {e}")

    async def stop(self, *args):
        await super().stop()
        if self.me:
            print(f"🛑 {self.me.first_name} Bot stopped.")
        else:
            print("🛑 Bot stopped.")

if __name__ == "__main__":
    Bot().run()
