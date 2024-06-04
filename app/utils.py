from database import get_db


async def save_chat_history(user_ask: str, assistant_answer: str, user_id: str, pdf_name: str = None):
    db = await get_db()
    collection = db['chat_history']
    if pdf_name:
        document = {"user_id": user_id, "user_ask": f"<pdf>{pdf_name}</pdf>", "assistant_answer": assistant_answer}
    else:
        document = {"user_id": user_id, "user_ask": user_ask, "assistant_answer": assistant_answer}
    result = await collection.insert_one(document)
    return result.inserted_id

def keep_recent_context(conversation_context, n):
    if len(conversation_context) < n * 2:
        return conversation_context
    recent_context = []
    for i in range(len(conversation_context) - n * 2, len(conversation_context), 2):
        recent_context.append(conversation_context[i])
        recent_context.append(conversation_context[i + 1])
    return recent_context