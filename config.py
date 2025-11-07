from os import environ

API_ID = int(environ.get("API_ID", "28079855"))
API_HASH = environ.get("API_HASH", "3493b73fe86e88f409ac7b95d23cff5b")
BOT_TOKEN = environ.get("BOT_TOKEN", "8421516268:AAHX-hFv4zLEWv1J49bQGOD3JyA3xEScMAg")

# Make Bot Admin In Log Channel With Full Rights
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1002073865889"))
ADMINS = int(environ.get("ADMINS", "1327021082"))

# Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_URI = environ.get("DB_URI", "mongodb+srv://satyadipdas24_db_user:HtkJpIxhDM3h1qKh@cluster0.o35rffc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") # Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_NAME = environ.get("DB_NAME", "vjlinkchangerbot")
