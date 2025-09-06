from core.entities.notification_preference import NotificationPreference, NotificationChannelPreference, \
    NotificationTypePreference
from core.entities.user import User
from core.interfaces.repositories.notification_preference_repository import NotificationPreferenceRepository
from core.interfaces.repositories.user_repository import UserRepository


class UserService:
    def __init__(self,
                 user_repository: UserRepository,
                 notification_preference_repository: NotificationPreferenceRepository):
        self.user_repository = user_repository
        self.notification_preference_repository = notification_preference_repository

    def create_user(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        self.user_repository.add(user)
        return user

    def login(self, user: User):
        # logic to login the user
        pass

    def get_user_by_id(self, user_id: str) -> User:
        return self.user_repository.find_by_id(user_id)

    def get_user_by_email(self, email: str) -> User:
        return self.user_repository.find_by_email(email)


    def add_notification_preference_for_user(self, user_id: str, channel_preference: list[NotificationChannelPreference], type_preference: list[NotificationTypePreference]) -> NotificationPreference:
        user = self.user_repository.find_by_id(user_id)
        notification_preference = NotificationPreference(
            user=user,
            channel_preference=channel_preference,
            type_preference=type_preference
        )
        self.notification_preference_repository.save(notification_preference)
        return notification_preference

    def get_notification_preference_for_user(self, user_id: str) -> NotificationPreference:
        notification_preference = self.notification_preference_repository.get_notification_preference_for_user_by_id(user_id)
        return notification_preference

