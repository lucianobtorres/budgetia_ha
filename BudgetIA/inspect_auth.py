
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import streamlit as st

# Mock config
config = {
    "credentials": {"usernames":{}},
    "cookie": {"name": "c", "key": "k", "expiry_days": 1}
}

try:
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    print("Attributes:", dir(authenticator))
    if hasattr(authenticator, 'validator'):
        print("Validator:", authenticator.validator)
except Exception as e:
    print("Error:", e)
