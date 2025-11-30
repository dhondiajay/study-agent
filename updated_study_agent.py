import os
import json
import google.generativeai as genai
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

class ExamPrepAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️  GEMINI_API_KEY not found in environment variables.")
            self.api_key = input("Please enter your Gemini API Key: ").strip()
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def search_videos(self, topic):
        print(f"🎥 Searching for videos on: {topic}...")
        with DDGS() as ddgs:
            # Search for videos
            videos = list(ddgs.videos(topic, max_results=1))
            if videos:
                return videos[0]
        return None

    def get_page_content(self, url):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            # Kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            # Get text
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:5000] # Limit to 5000 chars to avoid token limits
        except Exception as e:
            print(f"⚠️ Could not fetch content from {url}: {e}")
            return ""

    def search_topic(self, topic):
        print(f"\n🔍 Searching for: {topic}...")
        results = []
        with DDGS() as ddgs:
            # Get top 3 results
            search_results = list(ddgs.text(topic, max_results=3))
            for result in search_results:
                print(f"   Reading: {result['title']}...")
                content = self.get_page_content(result['href'])
                if content:
                    results.append(f"Title: {result['title']}\nURL: {result['href']}\nContent: {content}")
                else:
                    # Fallback to snippet if can't read page
                    results.append(f"Title: {result['title']}\nURL: {result['href']}\nSnippet: {result['body']}")
        
        return "\n\n".join(results)

    def summarize_content(self, topic, search_results):
        print("🧠 Analyzing and summarizing for exam prep...")
        prompt = f"""
        You are an expert exam tutor. Your goal is to help a student get high marks with minimal reading.
        
        Topic: {topic}
        
        Search Results:
        {search_results}
        
        Task:
        1. Extract the MOST important points from the search results.
        2. Format them as short, high-yield bullet points.
        3. Focus on keywords and concepts that are likely to appear in exams.
        4. Keep it concise.
        
        Output Format:
        ## 📝 Exam Cheat Sheet: {topic}
        
        * [Point 1]
        * [Point 2]
        ...
        """
        
        response = self.model.generate_content(prompt)
        return response.text

    def generate_quiz(self, topic, content):
        print("❓ Generating quiz questions...")
        prompt = f"""
        Based on the following content about "{topic}", generate 10 multiple-choice questions.
        
        Content:
        {content}
        
        Output Format (JSON):
        [
            {{
                "question": "Question text here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0  // Index of the correct option (0-3)
            }},
            ...
        ]
        """
        response = self.model.generate_content(prompt)
        return response.text

    def run_quiz(self, quiz_data):
        score = 0
        try:
            # Clean up markdown code blocks if present
            cleaned_data = quiz_data.replace("```json", "").replace("```", "").strip()
            questions = json.loads(cleaned_data)
            
            print(f"\n📝 Quiz Time! (10 Questions)")
            for i, q in enumerate(questions):
                print(f"\nQ{i+1}: {q['question']}")
                for j, opt in enumerate(q['options']):
                    print(f"   {chr(65+j)}) {opt}")
                
                ans = input("Your answer (A/B/C/D): ").strip().upper()
                correct_idx = q['correct_answer']
                correct_char = chr(65 + correct_idx)
                
                if ans == correct_char:
                    print("✅ Correct!")
                    score += 1
                else:
                    print(f"❌ Wrong. The correct answer was {correct_char}.")
            
            print(f"\n🏆 Quiz Finished! You scored {score}/{len(questions)}.")
            
        except Exception as e:
            print(f"⚠️ Could not start quiz: {e}")

    def run(self):
        print("🎓 Welcome to the Exam Prep Agent!")
        print("Type 'exit' to quit.\n")
        
        while True:
            topic = input("Enter a topic or question: ").strip()
            if topic.lower() == 'exit':
                break
            
            if not topic:
                continue
                
            try:
                search_data = self.search_topic(topic)
                video = self.search_videos(topic)
                
                if not search_data:
                    print("❌ No results found. Try a different topic.")
                    continue
                    
                summary = self.summarize_content(topic, search_data)
                print("\n" + "="*40)
                print(summary)
                
                if video:
                    print(f"\n📺 Recommended Video:")
                    print(f"Title: {video['title']}")
                    print(f"Link: {video['content']}")
                
                print("="*40 + "\n")

                # Quiz Section
                do_quiz = input("Do you want to take a quiz on this topic? (y/n): ").strip().lower()
                if do_quiz == 'y':
                    quiz_json = self.generate_quiz(topic, search_data)
                    self.run_quiz(quiz_json)
                
            except Exception as e:
                print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    try:
        agent = ExamPrepAgent()
        agent.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
