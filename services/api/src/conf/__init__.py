from pydantic import BaseModel

from utils import auth, env, log
from utils.env import EnvVarSpec

logger = log.get_logger(__name__)

# Set to True to enable authentication
USE_AUTH = False

#### Types ####

class HttpServerConf(BaseModel):
    host: str
    port: int
    autoreload: bool

#### Env Vars ####

## Logging ##

LOG_LEVEL = EnvVarSpec(id="LOG_LEVEL", default="INFO")

## HTTP ##

HTTP_HOST = EnvVarSpec(id="HTTP_HOST", default="0.0.0.0")

HTTP_PORT = EnvVarSpec(id="HTTP_PORT", default="8000")

HTTP_AUTORELOAD = EnvVarSpec(
    id="HTTP_AUTORELOAD",
    parse=lambda x: x.lower() == "true",
    default="false",
    type=(bool, ...),
)

HTTP_EXPOSE_ERRORS = EnvVarSpec(
    id="HTTP_EXPOSE_ERRORS",
    default="false",
    parse=lambda x: x.lower() == "true",
    type=(bool, ...),
)

## OpenRouter ##

OPENROUTER_API_KEY = EnvVarSpec(id="OPENROUTER_API_KEY", default="")

OPENROUTER_MODEL = EnvVarSpec(id="OPENROUTER_MODEL", default="tngtech/deepseek-r1t2-chimera:free")

OPENROUTER_BASE_URL = EnvVarSpec(id="OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

## LangSmith ##

LANGCHAIN_TRACING_V2 = EnvVarSpec(
    id="LANGCHAIN_TRACING_V2",
    default="false",
    parse=lambda x: x.lower() == "true",
    type=(bool, ...),
)

LANGCHAIN_API_KEY = EnvVarSpec(id="LANGCHAIN_API_KEY", default="")

LANGCHAIN_PROJECT = EnvVarSpec(id="LANGCHAIN_PROJECT", default="default")

#### Validation ####
VALIDATED_ENV_VARS = [
    HTTP_AUTORELOAD,
    HTTP_EXPOSE_ERRORS,
    HTTP_PORT,
    LOG_LEVEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
    LANGCHAIN_TRACING_V2,
    LANGCHAIN_API_KEY,
    LANGCHAIN_PROJECT,
]

def validate() -> bool:
    return env.validate(VALIDATED_ENV_VARS)

#### Getters ####

def get_http_expose_errors() -> str:
    return env.parse(HTTP_EXPOSE_ERRORS)

def get_log_level() -> str:
    return env.parse(LOG_LEVEL)

def get_http_conf() -> HttpServerConf:
    return HttpServerConf(
        host=env.parse(HTTP_HOST),
        port=env.parse(HTTP_PORT),
        autoreload=env.parse(HTTP_AUTORELOAD),
    )

def get_openrouter_api_key() -> str:
    return env.parse(OPENROUTER_API_KEY)

def get_openrouter_model() -> str:
    return env.parse(OPENROUTER_MODEL)

def get_openrouter_base_url() -> str:
    return env.parse(OPENROUTER_BASE_URL)

def get_langchain_tracing_v2() -> bool:
    return env.parse(LANGCHAIN_TRACING_V2)

def get_langchain_api_key() -> str:
    return env.parse(LANGCHAIN_API_KEY)

def get_langchain_project() -> str:
    return env.parse(LANGCHAIN_PROJECT)
