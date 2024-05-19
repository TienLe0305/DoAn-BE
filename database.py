import motor.motor_asyncio

client = None

async def connect_db(mongodb_uri):
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)

async def get_db():
    return client['DoAn']