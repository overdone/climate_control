from tg.bot import ClimateControlBot
import settings


def run():
    bot = ClimateControlBot(
        settings.BOT_TOKEN,
        settings.TELEGRAM_API_PROTO,
        settings.TELEGRAM_API_HOST,
        settings.TELEGRAM_API_PORT
    )
    bot.run()


run()
