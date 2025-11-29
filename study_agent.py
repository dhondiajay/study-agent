import google.generativeai as genai

class StudyAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def explain_topic(self, topic):
        prompt = f"Explain the topic '{topic}' in simple language for a student."
        response = self.model.generate_content(prompt)
        return response.text

    def generate_notes(self, topic):
        prompt = f"""
        Create short, exam-focused study notes for the topic: {topic}.
        Make them clear, bullet-point style, and easy to memorize.
        """
        response = self.model.generate_content(prompt)
        return response.text

    def generate_mcq(self, topic):
        prompt = f"""
        Generate 5 multiple-choice questions (MCQs) for the topic '{topic}'.
        Each question should have options A/B/C/D.
        Provide the correct answer as well.
        
        Output format:
        Q1) question?
        A) option
        B) option
        C) option
        D) option
        Correct Answer: A
        """
        response = self.model.generate_content(prompt)
        return response.text
