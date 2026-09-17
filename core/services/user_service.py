from core.security.authentication import hash_password
from data.repositories_impl.user_repository import UserRepository
from core.models.user import User, UserRole

class UserService:
    @staticmethod
    def create_admin_user(username: str, password: str, full_name: str):
        repo = UserRepository()
        if repo.get_by_username(username):
            return False
            
        admin = User(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        return repo.create(admin)