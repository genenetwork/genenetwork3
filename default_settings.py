"""module contains default settings for genenetwork"""
import os


USE_REDIS = True

GN2_BASE_URL = "https://genenetwork.org/"


HOME = os.environ['HOME']

# SQL_URI = "mysql://gn2:mysql_password@localhost/db_webqtl_s"

SQL_URI = os.environ.get("SQL_URI","mysql+pymysql://kabui:1234@localhost/db_webqtl")

SECRET_HMAC_CODE = '\x08\xdf\xfa\x93N\x80\xd9\\H@\\\x9f`\x98d^\xb4a;\xc6OM\x946a\xbc\xfc\x80:*\xebc'

GENENETWORK_FILES = os.environ.get("GENENETWORK_FILES",HOME+"/data/genotype_files")
