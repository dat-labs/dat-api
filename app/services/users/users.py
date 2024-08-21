import bcrypt
from ...db_models.users import User as UserModel
from ...db_models.workspace_users import WorkspaceUser
from ...db_models.workspaces import Workspace
from ...common.exceptions.exceptions import NotFound, Unauthorized

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
                    workspace_name = self.db_session.query(Workspace).filter(Workspace.id == workspace_id).first().name

                return {
                    "id": user.id,
                    "email": user.email,
                    "workspace_id": workspace_id,
                    "workspace_name": workspace_name,
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
