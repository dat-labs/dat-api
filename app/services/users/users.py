import bcrypt
from app.db_models.users import User as UserModel
from app.db_models.workspace_users import WorkspaceUser
from app.db_models.workspaces import Workspace
from app.common.exceptions.exceptions import NotFound, Unauthorized
from app.models.user_model import UserResponse

class Users():
    """
    Class for user-related operations.
    """

    def __init__(self, db_session):
        """
        Initializes the Users object with a database session.

        Parameters:
        - db_session: SQLAlchemy database session.
        """
        self.db_session = db_session

    def verify_user(self, email, password):
        """
        Verify user credentials.

        Parameters:
        - email (str): Email of the user to verify.
        - password (str): Password of the user to verify.

        Returns:
        - dict or None: Dictionary containing user information if credentials are valid.
        
        Raises:
        - NotFound: If user is not found.
        - Unauthorized: If user email and password do not match
        """
        user = self.db_session.query(UserModel).filter(UserModel.email == email).first()
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Fetch workspace_id from workspace_users table
                workspace_user = self.db_session.query(WorkspaceUser).filter(WorkspaceUser.user_id == user.id).first()
                if workspace_user:
                    workspace_id = workspace_user.workspace_id
                else:
                    workspace_id = None

                if workspace_id:
                    workspace = self.db_session.query(Workspace).filter(Workspace.id == workspace_id).first()
                    workspace_name = workspace.name
                    organization_id = workspace.organization_id

                return {
                    "id": user.id,
                    "email": user.email,
                    "workspace_id": workspace_id,
                    "workspace_name": workspace_name,
                    "organization_id": organization_id,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                }
            raise Unauthorized("Email and Password do not match")
        raise NotFound("User Not Found")

    def fetch_users(self):
        """
        Fetch all users.

        Returns:
        - list: List of all users.
        """
        try:
            users = self.db_session.query(UserModel).all()
            return users
        except Exception as e:
            raise NotFound(str(e))

    def create_user(self, email, password):
        """
        Create a new user.

        Parameters:
        - email (str): Email of the user to create.
        - password (str): Password of the user to create (hashed or plain).

        Returns:
        - dict: Dictionary containing user information.
        """
        if not is_hashed(password):
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = UserModel(email=email, password_hash=password)
        self.db_session.add(user)
        self.db_session.commit()
        return UserResponse(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    def update_user(self, user_id, email, password):
        """
        Update a user.

        Parameters:
        - user_id (str): ID of the user to update.
        - email (str): Email of the user to update.
        - password (str): Password of the user to update (hashed or plain).

        Returns:
        - dict: Dictionary containing updated user information.
        """
        user = self.db_session.query(UserModel).get(user_id)
        if user:
            if not is_hashed(password):
                password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.email = email
            user.password_hash = password
            self.db_session.commit()
            return UserResponse(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        raise NotFound("User Not Found")

def is_hashed(password: str) -> bool:
    """Check if the password is hashed."""
    return password.startswith('$2b$') or password.startswith('$2a$') and len(password) == 60
