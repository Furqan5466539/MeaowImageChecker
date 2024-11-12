# import os
# import json
# import re
# from dotenv import load_dotenv
# from openai import OpenAI
# import base64
# from prompt import get_prompt
# from PIL import Image
# from datetime import date


# load_dotenv()

# openai_api_key = os.getenv('OPENAI_API_KEY')
# model_id = os.getenv('MODEL_ID')
# client = OpenAI(api_key=openai_api_key)

# def save_result(keyword, trend_reason, score, reasoning, image_path):
#     results_dir = "./results"
#     os.makedirs(results_dir, exist_ok=True)
    
#     today = date.today().strftime('%Y%m%d')
#     filename = f"{results_dir}/{today}_{keyword.replace(' ', '_')}.json"

#     new_entry = {
#         "keyword": keyword,
#         "trending_reason": trend_reason,
#         "score": score,
#         "reasoning": reasoning,
#         "image_path": image_path
#     }

#     if os.path.exists(filename):
#         with open(filename, 'r') as f:
#             data = json.load(f)
#     else:
#         data = []

#     data.append(new_entry)

#     with open(filename, 'w') as f:
#         json.dump(data, f, indent=2)

# def check_image_relevance(keyword, trend_reason, image_path):
#     with Image.open(image_path) as img:
#         if img.mode != 'RGB':
#             img = img.convert('RGB')
#         temp_path = "temp_image.jpg"
#         img.save(temp_path, "JPEG")

#     with open(temp_path, "rb") as image_file:
#         encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

#     os.remove(temp_path)

#     prompt = get_prompt(keyword, trend_reason)

#     response = client.chat.completions.create(
#         model=model_id,
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": prompt},
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": f"data:image/jpeg;base64,{encoded_image}"
#                         }
#                     }
#                 ]
#             }
#         ],
#         max_tokens=300,
#         temperature=0,
#         response_format={"type": "json_object"}
#     )

#     result = response.choices[0].message.content
#     print("Raw AI response:")
#     print(result)

#     try:
#         # Remove any markdown-style code blocks
#         result_cleaned = re.sub(r'```json\s*|\s*```', '', result)
#         result_json = json.loads(result_cleaned)
#         score = int(result_json["score"])
#         reasoning = result_json["reasoning"]

#         # Save the result to a JSON file
#         save_result(keyword, trend_reason, score, reasoning, image_path)

#         return score, reasoning
#     except (json.JSONDecodeError, KeyError, ValueError) as e:
#         print(f"Error: Unable to parse the AI response as JSON. Error: {str(e)}")
#         return -1, "Error in processing the AI response."


import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
import base64
from io import BytesIO
from prompt import get_prompt
from PIL import Image
from datetime import date
import requests

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
model_id = os.getenv('MODEL_ID')
client = OpenAI(api_key=openai_api_key)

def save_result(keyword, trend_reason, score, reasoning, image_url):
    results_dir = "./results"
    os.makedirs(results_dir, exist_ok=True)
    
    today = date.today().strftime('%Y%m%d')
    filename = f"{results_dir}/{today}_{keyword.replace(' ', '_')}.json"

    new_entry = {
        "keyword": keyword,
        "trending_reason": trend_reason,
        "score": score,
        "reasoning": reasoning,
        "image_url": image_url  # Storing image URL instead of image path
    }

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
    else:
        data = []

    data.append(new_entry)

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def check_image_relevance(keyword, trend_reason, image_url):
    # Fetch the image directly from the URL for encoding
    response = requests.get(image_url)
    response.raise_for_status()  # Raise error if the request failed

    # Open image and convert it if necessary
    image = Image.open(BytesIO(response.content))
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Convert the image to base64 without saving to disk
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Get the prompt
    prompt = get_prompt(keyword, trend_reason)

    # Call the API with the image encoded directly from the URL
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300,
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = response.choices[0].message.content
    print("Raw AI response:")
    print(result)

    try:
        # Remove any markdown-style code blocks
        result_cleaned = re.sub(r'```json\s*|\s*```', '', result)
        result_json = json.loads(result_cleaned)
        score = int(result_json["score"])
        reasoning = result_json["reasoning"]

        # Save the result with image_url instead of image_path
        save_result(keyword, trend_reason, score, reasoning, image_url)

        return score, reasoning
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error: Unable to parse the AI response as JSON. Error: {str(e)}")
        return -1, "Error in processing the AI response."
