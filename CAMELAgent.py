import google.generativeai as genai
from typing import List, Optional, Dict
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)
import backoff
import os

# Configure the Gemini model
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

class PitchAnalyzer:
    def __init__(
        self,
        model: genai.GenerativeModel = model,
    ) -> None:
        self.model = model
        self.analysis_categories = {
            "Clarity": "Evaluate the clarity and structure of the pitch",
            "Market": "Analyze the market potential and opportunity",
            "Investor": "Assess investor appeal and investment readiness",
            "Improvements": "Suggest specific improvements and recommendations"
        }

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def analyze_pitch(self, pitch_text: str) -> Dict[str, str]:
        """Analyze the pitch text and return feedback for each category."""
        feedback = {}
        
        for category, description in self.analysis_categories.items():
            try:
                prompt = f"""
                {description}
                
                Pitch Text:
                {pitch_text}
                
                Provide a detailed analysis with specific examples from the pitch.
                Format your response with:
                1. Key Observations
                2. Strengths
                3. Areas for Improvement
                4. Specific Recommendations
                """
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=1024,
                    )
                )
                
                feedback[category] = response.text
                
            except Exception as e:
                print(f"Error analyzing {category}: {str(e)}")
                feedback[category] = f"Error analyzing {category}: {str(e)}"
        
        return feedback

class CAMELAgent:

    def __init__(
        self,
        system_message: SystemMessage,
        model: genai.GenerativeModel = model,
    ) -> None:
        self.system_message = system_message
        self.model = model
        self.init_messages()

    def reset(self) -> None:
        self.init_messages()
        return self.stored_messages

    def init_messages(self) -> None:
        self.stored_messages = [self.system_message]

    def update_messages(self, message: BaseMessage) -> List[BaseMessage]:
        self.stored_messages.append(message)
        return self.stored_messages

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def step(
        self,
        input_message: HumanMessage,
    ) -> AIMessage:
        try:
            messages = self.update_messages(input_message)
            
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    formatted_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    formatted_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    formatted_messages.append({"role": "model", "content": msg.content})
            
            response = self.model.generate_content(
                contents=[msg["content"] for msg in formatted_messages],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )
            
            output_message = AIMessage(content=response.text)
            self.update_messages(output_message)
            return output_message
            
        except Exception as e:
            print(f"Error in CAMELAgent step: {str(e)}")
            raise e
