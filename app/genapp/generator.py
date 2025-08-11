# views.py
import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import json

# Configure the API at the module level
try:
    genai.configure(api_key=config("GEMINI_API_KEY"))
    MODEL = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring GenerativeAI: {e}")

# Pitch Reply Generator
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
        response = MODEL.generate_content(prompt)
        
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

# Article Generator
def generate_article_titles(tool_details, extra_ideas):
    """
    Calls the Gemini API to generate article titles and handles potential errors.
    Returns a JSON string containing a list of title options.
    """
    user_prompt = f"""
    You are an expert SaaS content marketer and SEO specialist, with a specific focus on product and e-commerce content. Your goal is to generate a list of helpful, engaging, and SEO-optimized article titles and corresponding meta descriptions. These articles are designed to help a specific product rank higher on search engines and attract potential customers.

    ### Instructions:
    1.  **Generate Multiple Options:** Provide at least **four** different title and meta description pairs.
    2.  **Product-Centric SEO Titles:**
        - **Highlight Benefits:** Titles should focus on the problem the product solves or the benefit it provides to the user.
        - **Target Keywords:** Titles must be crafted around keywords people would use to find a solution like this product. Prioritize long-tail keywords that are specific to the product's function. If a specific keyword isn't provided in "extra ideas," you must generate one based on the `tool_details`.
        - **Character Limits:** Titles should be between 50-75 characters long to avoid truncation in search engine results.
        - **Evoke Curiosity/Trust:** Use power words (e.g., "ultimate," "essential," "proven") or numbers/lists (e.g., "5 Ways," "The Top 10") to increase click-through rate (CTR).
    3.  **Compelling Meta Descriptions:**
        - Descriptions must be between 150-160 characters long.
        - They should be a brief, compelling summary that reinforces the product's value and includes a call-to-action (e.g., "Discover how," "Learn more").
        - The description should encourage a click by promising a solution to the reader's problem.
    4.  **Tone & Style:** The tone should be engaging and authoritative, building trust in the product as the ultimate solution.

    ### Product Details (The source of truth for the article):
    {tool_details}
    
    ### Extra Angle or Ideas to Consider:
    {extra_ideas if extra_ideas else 'N/A'}

    ### Output Format:
    You must provide your final output in a single JSON object. The `titles` key should contain a list of objects, each with a `title` and `description`. Do not add any text before or after the JSON.

    Example:
    ```json
    [
        {{
          "title": "A Compelling Title Option 1 (50-75 chars)",
          "description": "A brief, 150-160 character description for search engine results."
        }},
        {{
          "title": "Another Strong Title Idea for SEO",
          "description": "A second, equally powerful meta description to attract clicks."
        }},
        {{
          "title": "A Third Option with a Creative Twist",
          "description": "The final description focuses on a unique benefit or angle."
        }}
    ]
    ```
    """
    try:
        response = MODEL.generate_content(user_prompt)
        # This is the crucial part: Safely access and process the text
        json_string = response.text.strip().replace('```json', '').replace('```', '').strip()
        
        # Safely parse the JSON string into a Python dictionary
        items = json.loads(json_string)

        return items
    
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from AI: {e}")
        return {"error": "Generated content was in an invalid JSON format."}
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": "An error occurred while communicating with the API."}

def article_generator(tool_details, extra_ideas):
    """
    Calls the Gemini API to generate an article and handles potential errors.
    Returns a tuple: (is_success, content).
    """
    user_prompt = f"""
    You are an expert SaaS content marketer and SEO specialist. Your goal is to write a helpful, engaging, and SEO-optimized article based on the provided product details and user ideas.

    ### Instructions:
    1.  **Persona & Tone:** Write in a clear, natural, and helpful tone. Be professional and knowledgeable, not overly formal or robotic.
    2.  **SEO Focus:** Your primary goal is to create an article that will rank well.
        - **Target Keyword:** If the user has not provided a keyword in their extra ideas, you must generate a relevant, high-traffic keyword from the product details. Use this keyword and related terms naturally throughout the article.
        - **Length:** The article should be concise, ideally between 500-700 words, to make it easy for readers to digest.
    3.  **Content & Structure:**
        - The article must focus on the benefits and features of the product.
        - Start with an engaging headline and a short intro.
        - Use clear subheadings (##) to organize the content.
        - Use bullet points or numbered lists where appropriate to make ideas easy to skim.
    4.  **Source & Trust:** All information must come directly from the provided product details. Do not invent or hallucinate external sources. The goal is to build trust in the product itself.
    5.  **User Ideas:** Incorporate the "Extra Angle or Ideas" to guide the tone, narrative, and specific talking points.
    6.  **Formatting:**
        - Do not mention that this was written by AI.
        - Do not include disclaimers or generic phrases like "in conclusion."
        - Format the final output as a JSON object with three keys: `title`, `seo_description`, and `content`. The content must be in valid Markdown.

    ### Product Details:
    {tool_details}

    ### Extra Angle or Ideas to Consider:
    {extra_ideas if extra_ideas else 'None'}

    ### Output Format:
    You must provide your final output in the following JSON format. Do not add any text before or after the JSON.
    ```json
    [
      {
        "title": "A Compelling Title for the Article",
        "seo_description": "A brief, 150-160 character description for search engine results.",
        "content": "... a detailed article in MARKDOWN format with headings, bolding, and lists."
      }
    ]
    ```
    """
    try:
        response = MODEL.generate_content(user_prompt)
        # This is the crucial part: Safely access the text
        article = response.text.strip()
        return json.loads(article)
    except ValueError:
        # This error occurs if content is blocked by safety filters
        print("Response was blocked by safety filters.")
        # You can inspect response.prompt_feedback here for details
        return "Generated content was blocked for safety reasons."
    except Exception as e:
        # Handle other potential API errors (e.g., network issues, invalid key)
        print(f"An unexpected error occurred: {e}")
        return "An error occurred while communicating with the API."


# # Tweet Hook Generator
# def tweet_hook_generator(tool_details, extra_ideas):
#     """
#     Calls the Gemini API to generate tweet hook ideas and handles potential errors.
#     Returns a JSON list of hooks.
#     """
#     user_prompt = f"""
#     You are a social media copywriting expert with a deep understanding of Twitter/X engagement strategies.
#     Your goal is to create short, attention-grabbing tweet hooks to promote a specific product or tool.

#     ### Instructions:
#     1. **Generate Multiple Options:** Provide at least **five** unique tweet hook ideas.
#     2. **Hook Style:**
#         - Keep them under **100 characters** (short enough for Twitter/X to make them instantly scannable).
#         - Use curiosity, urgency, or bold statements to stop scrolling.
#         - Where relevant, use emojis for emphasis, but not in every hook.
#         - Avoid hashtags unless highly relevant and minimal (1-2 max).
#     3. **Product-Centric Messaging:**
#         - Highlight the problem the product solves or the key benefit.
#         - Make it relatable to the target audience.
#         - If no specific extra ideas are given, infer the best possible angle from the `tool_details`.
#     4. **Tone & Style:**
#         - Conversational, punchy, and engaging.
#         - Optional use of lists, numbers, or hooks like "What nobody tells you about..." or "The secret to...".
#     5. **Do NOT include links** — these are just hook starters for tweets.

#     ### Product Details:
#     {tool_details}

#     ### Extra Angle or Ideas to Consider:
#     {extra_ideas if extra_ideas else 'N/A'}

#     ### Output Format:
#     You must return only a JSON array of strings — each string is a single tweet hook idea.

#     Example:
#     ```json
#     [
#         "🚀 Boost your sales without spending more on ads",
#         "The 3-step trick to doubling your productivity",
#         "Why marketers can’t stop talking about this tool",
#         "Your competitors don’t want you to see this",
#         "One tweak that changes everything for {product_name}"
#     ]
#     ```
#     """

#     try:
#         response = MODEL.generate_content(user_prompt)
#         json_string = response.text.strip().replace('```json', '').replace('```', '').strip()
#         hooks = json.loads(json_string)
#         return hooks

#     except json.JSONDecodeError as e:
#         print(f"Error decoding JSON from AI: {e}")
#         return {"error": "Generated content was in an invalid JSON format."}

#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return {"error": "An error occurred while communicating with the API."}


