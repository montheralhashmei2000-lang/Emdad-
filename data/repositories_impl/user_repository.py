from data.repositories_impl.base_sqlite_repository import BaseSQLiteRepository
from data.database import get_session
from data.orm_models import UserModel
from core.models.user import User


class UserRepository(BaseSQLiteRepository[User]):
    def __init__(self):
        session = get_session()
        super().__init__(session, UserModel, User, "user")

    def get_by_username(self, username: str):
        obj = self.session.query(self.orm_class).filter(
            self.orm_class.username == username,
            self.orm_class.is_deleted == 0,
        ).first()
        if obj is None:
            return None
        return self._orm_to_pydantic(obj)