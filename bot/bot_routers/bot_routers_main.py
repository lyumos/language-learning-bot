from bot.bot_routers.word_processing_routers import WordProcessingRouters
from bot.bot_routers.quiz_routers import QuizRouters
from bot.bot_routers.settings_routers import SettingsRouters
from bot.bot_routers.extra_features_routers import ExtraFeaturesRouters
from aiogram import Router, Bot
import os


class BotRouters:

    def __init__(self):
        self.router = Router()
        self.bot_token = os.getenv('BOT_TOKEN')
        self.bot = Bot(token=self.bot_token)
        self._initialize_routers()

    def _initialize_routers(self):
        word_processing_routers = WordProcessingRouters()
        quiz_routers = QuizRouters()
        settings_routers = SettingsRouters()
        extra_features_routers = ExtraFeaturesRouters()

        self.router.include_router(word_processing_routers.router)
        self.router.include_router(quiz_routers.router)
        self.router.include_router(settings_routers.router)
        self.router.include_router(extra_features_routers.router)