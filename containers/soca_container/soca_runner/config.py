import os

FILE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(FILE_DIR, ".."))

TOKEN = os.getenv("GITHUB_TOKEN")