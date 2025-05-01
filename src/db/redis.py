import redis.asyncio as redis
from src.config import config

JTI_EXPIRY = 3600

token_blocklist = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    decode_responses=True
)

async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(jti, "", ex=JTI_EXPIRY)

async def token_in_blocklist(jti: str) -> bool:
    jti_in_blocklist = await token_blocklist.get(jti)
    return jti_in_blocklist is not None
