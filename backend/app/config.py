"""
Configuration management for the Enterprise RAG Chatbot

This reads settings from the .env file and provides them as a typed, validated Python
object. If a required variable is missing or the wrong type, you'll get a clear error on 
startup.
"""

# functools provides lru_cache -> a decorator to cache the result of a function call, useful for expensive operations like loading config   
import os
from functools import lru_cache

# BaseSettings reads environment variables automatically, SettingsConfigDict lets us configure WHERE to read the .env file
from pydantic_settings import BaseSettings, SettingsConfigDict

_dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

class Settings(BaseSettings):
    """ Application settings loaded from environment variables or .env file 
        How it works:
        -> Each field below maps to an environment variable
        -> Field name 'google_api_key' -> env var 'GOOGLE_API_KEY' [auto-converted]
        -> Pydantic validates the types [str stays str, int gets parsed from string]
        -> Default values are used if the env var dosen't exist
    """

    # Application INFO
    app_name: str = "Enterprise RAG Chatbot"
    app_version: str = "1.0.0"

    #API KEYS
    google_api_key: str = ""

    #Server Settings
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    debug: bool = True

    # Tell Pydantic to read from .env file in the backend root
    model_config = SettingsConfigDict(env_file=_dotenv_path, env_file_encoding="utf-8", extra="ignore")

# The @lru_cache decorator means this function runs ONCE, then returns the cached result for all future calls. This is the singleton pattern only one Settings object ever exists.
@lru_cache()
def get_settings() -> Settings:
    return Settings()

