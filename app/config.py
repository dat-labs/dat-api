from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

GITBOOK_ACCESS_TOKEN = os.getenv("GITBOOK_ACCESS_TOKEN")
GITBOOK_SPACE_ID = os.getenv("GITBOOK_SPACE_ID")
