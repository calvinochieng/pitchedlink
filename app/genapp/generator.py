# views.py
import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import json

# Configure the API at the module level
try:
    genai.configure(api_key=config("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error configuring GenerativeAI: {e}")

def generate_pitch(tool_details, tweet_content, extra_ideas):
    """
    Calls the Gemini API to generate a pitch and handles potential errors.
    Returns a tuple: (is_success, content).
    """
    prompt = f"""
        You are a creative SaaS marketer. Write a concise, engaging reply (max 40 words) to the following tweet, pitching the product described below. 

        Your reply should:
        - Seamlessly fit as a comment under the tweet.
        - Clearly mention the tool name, what it does, and its website link.
        - Use a friendly, attention-grabbing tone.
        - Optionally use a relevant emoji.
        - If helpful, incorporate these extra ideas: {extra_ideas if extra_ideas else 'N/A'}

        Tweet to reply to:
        \"\"\"{tweet_content}\"\"\"

        Product details:
        {tool_details}

        NOTE: Make your content to be like you're replying to the tweet, you dont have to follow the restrictions like when they say something like in 3 words or something in that style.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # This is the crucial part: Safely access the text
        pitch = response.text.strip()
        return (pitch)
        
    except ValueError:
        # This error occurs if content is blocked by safety filters
        print("Response was blocked by safety filters.")
        # You can inspect response.prompt_feedback here for details
        return ("Generated content was blocked for safety reasons.")
        
    except Exception as e:
        # Handle other potential API errors (e.g., network issues, invalid key)
        print(f"An unexpected error occurred: {e}")
        return ("An error occurred while communicating with the API.")

