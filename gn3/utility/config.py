class Config:
    DEBUG = True
    Testing = False


class DevConfig(Config):
    Testing = True
    SQLALCHEMY_DATABASE_URI = "mysql://kabui:1234@localhost/test"
    SECRET_KEY = "password"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def get_config():
    return {
        "dev": DevConfig
    }
