import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'b9a8bd545b2265939a1216abf1b76193')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.elaqzrcvbknbzvbkdwgp:iCcxsx4TpDLdwqzq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TELEGRAM_API_TOKEN = '7514207604:AAE_p_eFFQ3yOoNn-GSvTSjte2l8UEHl7b8'
