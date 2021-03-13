"""module for hmac """

# pylint: disable-all
import hmac
import hashlib

# xtodo work on this file

# from main import app


def hmac_creation(stringy):
    """Helper function to create the actual hmac"""

    # secret = app.config['SECRET_HMAC_CODE']
    # put in config
    secret = "my secret"
    hmaced = hmac.new(bytearray(secret, "latin-1"),
                      bytearray(stringy, "utf-8"),
                      hashlib.sha1)
    hm = hmaced.hexdigest()
    # ZS: Leaving the below comment here to ask Pjotr about
    # "Conventional wisdom is that you don't lose much in terms of security if you throw away up to half of the output."
    # http://www.w3.org/QA/2009/07/hmac_truncation_in_xml_signatu.html
    hm = hm[:20]
    return hm


def data_hmac(stringy):
    """Takes arbitrary data string and appends :hmac so we know data hasn't been tampered with"""
    return stringy + ":" + hmac_creation(stringy)


def url_for_hmac(endpoint, **values):
    """Like url_for but adds an hmac at the end to insure the url hasn't been tampered with"""

    url = url_for(endpoint, **values)

    hm = hmac_creation(url)
    if '?' in url:
        combiner = "&"
    else:
        combiner = "?"
    return url + combiner + "hm=" + hm



# todo
# app.jinja_env.globals.update(url_for_hmac=url_for_hmac,
#                              data_hmac=data_hmac)
