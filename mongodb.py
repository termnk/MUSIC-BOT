"""
We only use it to track unique users so we know when someone is new.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

_client: AsyncIOMotorClient | None = None
_users  = None
_banned = None
_db     = None  # ← module-level db reference


async def connect():
    global _client, _db, _users, _banned
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not set — add it to your environment variables")
    _client = AsyncIOMotorClient(MONGO_URI)
    _db     = _client[DB_NAME]
    _users  = _db["users"]
    _banned = _db["banned"]
    await _users.create_index("user_id", unique=True)
    print(f"[mongodb] connected → {DB_NAME}")


async def disconnect():
    global _client
    if _client:
        _client.close()
        print("[mongodb] disconnected")


async def is_new_user(user_id: int) -> bool:
    doc = await _users.find_one({"user_id": user_id}, {"_id": 1})
    return doc is None


async def add_user(user_id: int, first_name: str, username: str | None, dc_id: int | None):
    await _users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id":    user_id,
                "first_name": first_name,
                "username":   username,
                "dc_id":      dc_id,
            }
        },
        upsert=True,
    )


async def ban_user(user_id: int):
    await _banned.update_one({"_id": user_id}, {"$set": {"_id": user_id}}, upsert=True)


async def unban_user(user_id: int):
    await _banned.delete_one({"_id": user_id})


async def is_banned(user_id: int) -> bool:
    return await _banned.find_one({"_id": user_id}) is not None


async def get_all_users() -> list:
    return [doc["user_id"] async for doc in _users.find({}, {"user_id": 1})]
