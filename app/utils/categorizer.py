# categorizer.py
from decouple import config
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import re
import json
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

class PitchCategorizer:
    def __init__(self):
        self.api_key = config("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash"
        self.google_search_tool = Tool(google_search=GoogleSearch())
        
        # Predefined categories for consistency
        self.categories = [
            "SaaS",
            "E-commerce", 
            "Productivity Tool",
            "AI/ML",
            "Web Development",
            "Mobile App",
            "Marketing Tool",
            "Analytics",
            "Design Tool",
            "Development Tool",
            "Social Media",
            "Fintech",
            "EdTech",
            "HealthTech",
            "DevOps",
            "Gaming",
            "Content Creation",
            "Other"
        ]

    def scrape_website_content(self, url):
        """Scrape comprehensive content from website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract different content types
            content = {
                'title': soup.title.string.strip() if soup.title else "",
                'headings': [],
                'paragraphs': [],
                'features': [],
                'pricing_info': "",
                'about_text': ""
            }
            
            # Get headings (h1, h2, h3)
            for heading in soup.find_all(['h1', 'h2', 'h3'])[:10]:
                if heading.get_text().strip():
                    content['headings'].append(heading.get_text().strip())
            
            # Get paragraph content
            for p in soup.find_all('p')[:15]:
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short paragraphs
                    content['paragraphs'].append(text)
            
            # Look for feature lists
            for ul in soup.find_all(['ul', 'ol'])[:5]:
                for li in ul.find_all('li')[:8]:
                    feature = li.get_text().strip()
                    if feature and len(feature) > 10:
                        content['features'].append(feature)
            
            # Look for pricing-related content
            pricing_keywords = ['pricing', 'price', 'plan', 'subscription', 'cost', '$']
            for element in soup.find_all(text=True):
                text = element.strip().lower()
                if any(keyword in text for keyword in pricing_keywords) and len(text) > 20:
                    content['pricing_info'] = element.strip()[:200]
                    break
            
            # Look for about/description content
            about_sections = soup.find_all(['div', 'section'], class_=re.compile(r'about|description|intro', re.I))
            for section in about_sections[:3]:
                text = section.get_text().strip()
                if text and len(text) > 50:
                    content['about_text'] = text[:500]
                    break
            
            return content
            
        except Exception as e:
            print(f"Error scraping content from {url}: {e}")
            return None

    def generate_content(self, prompt):
        """Helper method to generate content using Gemini API"""
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=GenerateContentConfig(
                    tools=[self.google_search_tool],
                    response_modalities=["TEXT"],
                )
            )
            return response
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

    def extract_json(self, text):
        """Extract and parse JSON from Gemini response"""
        try:
            # Clean up the JSON text
            if "```json" in text:
                match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                if match:
                    text = match.group(1)
            elif "```" in text:
                match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
                if match:
                    text = match.group(1)
            
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            print(f"JSON extraction error: {str(e)}")
            return None

    def categorize_pitch(self, name, description, website_content, pitch_text=""):
        """Categorize a pitch using AI analysis"""
        
        # Prepare content for analysis
        content_summary = ""
        if website_content:
            content_summary = f"""
            Website Title: {website_content.get('title', '')}
            Headings: {' | '.join(website_content.get('headings', [])[:5])}
            Key Features: {' | '.join(website_content.get('features', [])[:8])}
            About: {website_content.get('about_text', '')[:300]}
            """
        
        prompt = f"""
        Analyze the following product/service and categorize it into ONE of these categories:
        {', '.join(self.categories)}
        
        Product Information:
        - Name: {name}
        - Description: {description}
        - Social Media Pitch: {pitch_text}
        - Website Content: {content_summary}
        
        Respond with ONLY the category name from the list above. Choose the most specific and accurate category.
        """
        
        response = self.generate_content(prompt)
        if response and response.text:
            category = response.text.strip()
            # Validate category is in our list
            if category in self.categories:
                return category
            else:
                # Try to find closest match
                for cat in self.categories:
                    if cat.lower() in category.lower():
                        return cat
        
        return "Other"  # Default fallback

    def generate_pitch_content(self, name, description, website_content, pitch_data_list):
        """Generate comprehensive content about the pitch"""
        
        # Analyze all pitch data for trends
        total_engagement = {"replies": 0, "retweets": 0, "likes": 0, "views": 0}
        users_mentioned = []
        
        for pitch in pitch_data_list:
            engagement = pitch.get("engagement", {})
            for key in total_engagement:
                total_engagement[key] += engagement.get(key, 0)
            
            user = pitch.get("user", {})
            if user.get("name"):
                users_mentioned.append(user["name"])
        
        # Prepare website content summary
        content_summary = ""
        if website_content:
            content_summary = f"""
            Website Analysis:
            - Title: {website_content.get('title', '')}
            - Key Features: {'; '.join(website_content.get('features', [])[:5])}
            - About: {website_content.get('about_text', '')[:200]}
            - Main Headings: {'; '.join(website_content.get('headings', [])[:3])}
            """
        
        prompt = f"""
        Generate comprehensive information about this product/service in JSON format:
        
        Product Details:
        - Name: {name}
        - Description: {description}
        - Total Social Engagement: {total_engagement}
        - Mentioned by {len(users_mentioned)} users
        - Website Content: {content_summary}
        
        Generate a JSON response with the following structure:
        {{
            "summary": "A 2-3 sentence summary of what this product does",
            "key_features": ["feature1", "feature2", "feature3"],
            "target_audience": "Who this product is for",
            "value_proposition": "Main value/benefit offered",
            "market_position": "How it positions itself in the market",
            "social_sentiment": "Based on social media mentions, what's the sentiment",
            "growth_indicators": "Analysis of engagement and mention patterns"
        }}
        
        Make the content informative and professional. Base insights on the provided data.
        """
        
        response = self.generate_content(prompt)
        if response and response.text:
            result = self.extract_json(response.text)
            if result:
                return result
        
        # Fallback basic content
        return {
            "summary": f"{name} - {description[:100]}",
            "key_features": [],
            "target_audience": "General users",
            "value_proposition": "Provides value to users",
            "market_position": "Emerging product",
            "social_sentiment": "Neutral",
            "growth_indicators": f"Mentioned by {len(users_mentioned)} users with {total_engagement['likes']} total likes"
        }

    def analyze_pitch_complete(self, name, description, url, pitch_data_list):
        """Complete analysis of a pitch - categorization and content generation"""
        try:
            # Step 1: Scrape website content
            print(f"Scraping content for {name}...")
            website_content = self.scrape_website_content(url)
            
            # Step 2: Categorize
            print(f"Categorizing {name}...")
            pitch_text = pitch_data_list[0].get("tweetText", "") if pitch_data_list else ""
            category = self.categorize_pitch(name, description, website_content, pitch_text)
            
            # Step 3: Generate comprehensive content
            print(f"Generating content for {name}...")
            generated_content = self.generate_pitch_content(name, description, website_content, pitch_data_list)
            
            return {
                "category": category,
                "website_content": website_content,
                "generated_content": generated_content,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in complete analysis: {e}")
            return {
                "category": "Other",
                "website_content": None,
                "generated_content": None,
                "analysis_timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# Usage example:
# categorizer = PitchCategorizer()
# result = categorizer.analyze_pitch_complete(name, description, url, pitch_data_list)