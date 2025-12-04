import msal
import os
from dotenv import load_dotenv

# Load environment variables from .env (Render will inject them automatically)
load_dotenv()

# Read environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

if not CLIENT_ID or not CLIENT_SECRET or not TENANT_ID:
    raise Exception("Missing CLIENT_ID, CLIENT_SECRET, or TENANT_ID in environment variables.")

# Microsoft OAuth settings
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]


def get_access_token():
    """
    Authenticate with Microsoft Graph using Client Credentials.
    This requires:
      - App registration in Azure
      - Application permissions granted
      - Admin consent granted
      - ApplicationAccessPolicy configured for the service mailbox
    """
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    # Try to get token from cache (recommended)
    token = app.acquire_token_silent(SCOPE, account=None)

    # If no cache, request a new token
    if not token:
        token = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" not in token:
        raise Exception(f"Authentication failed: {token}")

    return token["access_token"]
