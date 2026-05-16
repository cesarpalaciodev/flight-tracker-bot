
from src.models.database import Database, Subscription, UserConfig


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_or_create(self, chat_id: str) -> UserConfig:
        return self.db.get_or_create_user(chat_id)

    def get_by_chat_id(self, chat_id: str) -> UserConfig | None:
        return self.db.get_user_config(chat_id)

    def update(self, chat_id: str, **kwargs) -> UserConfig:
        return self.db.set_user_config(chat_id, **kwargs)

    def get_all_active(self) -> list[UserConfig]:
        return self.db.get_all_active_users()

    def get_subscription(self, chat_id: str) -> Subscription | None:
        return self.db.get_subscription(chat_id)

    def set_subscription(self, chat_id: str, **kwargs) -> Subscription:
        return self.db.set_subscription(chat_id, **kwargs)
