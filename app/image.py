from fastapi import APIRouter, UploadFile, File
import io
from PIL import Image
import logging
from transformers import BlipProcessor, BlipForConditionalGeneration
import asyncio

router = APIRouter()

blip_model_id = "Salesforce/blip-image-captioning-base"
processor = BlipProcessor.from_pretrained(blip_model_id)
blip_model = BlipForConditionalGeneration.from_pretrained(blip_model_id)

def generate_image_caption(image: Image.Image) -> str:
    inputs = processor(images=image, return_tensors="pt")
    out = blip_model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    return caption

def get_image_description(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")

        caption = generate_image_caption(image)
        print(caption)

        return caption
    except Exception as e:
        raise


@router.post("/ext/upload_image")
async def upload_image(image: UploadFile = File(...)):

    try:
        image_data = await image.read()

        description = await asyncio.to_thread(get_image_description, image_data)
        return {"description": description}
    except Exception as e:
        return {"error": str(e)}


