from pydantic import BaseModel
from bson import json_util
import json

class URLRequest(BaseModel):
    url: str

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        return json_util.default(o)