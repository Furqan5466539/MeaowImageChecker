
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os
from image_checker import check_image_relevance
import utils
from openai import OpenAI

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()

@app.post("/match-image/")
async def analyze_image(
    Keyword: str = Form(..., description="The name of the topic to be analyzed"),
    trending_reason: str = Form(..., description="The trending reason for the topic"),
    image_url: str = Form(..., description="URL of the image to be analyzed")
):
    """
    Analyze the relevance of an uploaded image based on the provided topic name and trend reason.
    """

    try:
        # Verify that the URL points to an image
        response = requests.head(image_url)
        if 'image' not in response.headers.get('Content-Type', ''):
            raise HTTPException(status_code=400, detail="The URL does not point to a valid image file.")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify image URL: {e}")

    # Process the image URL to check relevance
    try:
        score, reasoning = check_image_relevance(Keyword, trending_reason, image_url)  # Pass image_url instead of image_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

    # Prepare and return the result
    result = {
        "topic_name": Keyword,
        "trend_reason": trending_reason,
        "image_url": image_url,
        "relevance_score": score,
        "reasoning": reasoning
    }

    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
