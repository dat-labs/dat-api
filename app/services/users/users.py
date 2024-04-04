import bcrypt
from ...db_models.users import User as UserModel
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
                return user
            raise Unauthorized("Email and Password do not match")
        raise NotFound("User Not Found")
