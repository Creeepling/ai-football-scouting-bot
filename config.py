import os
import wyscoutapi

# ------------------------------------------------------------------------------
# API & Secret Configuration
# ------------------------------------------------------------------------------
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if SERPER_API_KEY:
    os.environ["SERPER_API_KEY"] = SERPER_API_KEY
else:
    print("Warning: SERPER_API_KEY is not set.")

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
else:
    print("Warning: OPENAI_API_KEY is not set.")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "127932719"))

# Model Configuration
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3-flash-preview")

# Wyscout Credentials
WYSCOUT_USERNAME = os.getenv("WYSCOUT_USERNAME")
WYSCOUT_PASSWORD = os.getenv("WYSCOUT_PASSWORD")

# MongoDB Credentials
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST", "analyticalplatform.cnoaz.mongodb.net")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "analyticalplatform")

# Google Cloud Storage Bucket
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "llmpafosfc")

# ------------------------------------------------------------------------------
# Position Groups Configuration
# ------------------------------------------------------------------------------
POS_GROUPS = {
    "goalkeeper": ["GK"],
    "winger": ["LWF", "RWF", "LW", "RW"],
    "attacking midfielder / second striker": ["AMF", "RAMF", "LAMF", "SS"],
    "central midfielder": ["LCMF3", "RCMF3", "LCMF", "RCMF", "LDMF", "RDMF", "DMF"],
    "central defender": ["CB", "RCB3", "LCB3", "LCB", "RCB"],
    "full back": ["RB", "LB", "RB5", "LB5", "RWB", "LWB"],
    "striker": ["CF"]
}


def get_wyscout_client():
    """Initializes and returns an authenticated Wyscout API client."""
    if not WYSCOUT_USERNAME or not WYSCOUT_PASSWORD:
        print("Warning: Wyscout credentials not configured, instantiating unauthenticated client.")
        return wyscoutapi.WyscoutAPI()
    else:
        return wyscoutapi.WyscoutAPI(
            username=WYSCOUT_USERNAME,
            password=WYSCOUT_PASSWORD,
        )
