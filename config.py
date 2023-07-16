import os

# Get environment secret GLOBALS
if not os.getenv("AWS_ACCESS_KEY_ID"):
    raise RuntimeError("AWS_ACCESS_KEY_ID is not set")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")

if not os.getenv("AWS_SECRET_ACCESS_KEY"):
    raise RuntimeError("AWS_SECRET_ACCESS_KEY is not set")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")