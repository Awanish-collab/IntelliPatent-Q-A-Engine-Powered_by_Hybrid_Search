# backend/followup_helper.py
import re
from typing import Dict, List, Optional
from .gemini_helper import gemini_model, generation_config

def analyze_followup_relationship(current_query: str, previous_query: str, previous_results: List[Dict]) -> Dict[str, any]:
    """
    Advanced analysis to determine if current query is a follow-up and its relationship strength.
    Uses Gemini to understand context and relationship between queries.
    """
    try:
        prompt = f"""
        You are an expert at analyzing conversational context in a patent Q&A system.
        
        Analyze the relationship between these two queries:
        
        Previous Query: "{previous_query}"
        Current Query: "{current_query}"
        
        Determine:
        1. Is the current query a follow-up to the previous one? (yes/no)
        2. Relationship strength (high/medium/low)
        3. What type of follow-up is it?
           - clarification: asking for more details about same topic
           - expansion: asking about related aspects
           - specific: asking about specific part mentioned in results
           - comparison: asking to compare or contrast
           - application: asking about uses or applications
           - none: not a follow-up
        
        Respond in this exact format:
        is_followup: yes/no
        strength: high/medium/low
        type: [one of the types above]
        confidence: [0.0 to 1.0]
        """
        
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        
        if not response or not hasattr(response, "text"):
            return {"is_followup": False, "strength": "low", "type": "none", "confidence": 0.0}
        
        # Parse response
        text = response.text.strip().lower()
        result = {
            "is_followup": "yes" in text.split("is_followup:")[1].split("\n")[0],
            "strength": "high" if "high" in text else ("medium" if "medium" in text else "low"),
            "type": "none",
            "confidence": 0.0
        }
        
        # Extract type
        if "clarification" in text:
            result["type"] = "clarification"
        elif "expansion" in text:
            result["type"] = "expansion"
        elif "specific" in text:
            result["type"] = "specific"
        elif "comparison" in text:
            result["type"] = "comparison"
        elif "application" in text:
            result["type"] = "application"
        
        # Extract confidence
        try:
            confidence_match = re.search(r"confidence:?\s*([0-9.]+)", text)
            if confidence_match:
                result["confidence"] = float(confidence_match.group(1))
        except:
            result["confidence"] = 0.5
        
        return result
    
    except Exception as e:
        print(f"❌ Follow-up analysis error: {e}")
        return {"is_followup": False, "strength": "low", "type": "none", "confidence": 0.0}

def generate_contextual_response(query: str, previous_results: List[Dict], followup_type: str) -> str:
    """
    Generate a contextual response based on previous results and follow-up type.
    """
    try:
        # Combine previous results content
        combined_content = ""
        for result in previous_results:
            combined_content += f"Patent: {result.get('patent_number', 'Unknown')}\n"
            combined_content += f"Title: {result.get('title', 'No title')}\n"
            combined_content += f"Summary: {result.get('detailed_summary', 'No summary')}\n\n"
        
        if not combined_content.strip():
            return "I don't have enough context from the previous search to answer your follow-up question."
        
        # Create specialized prompts based on follow-up type
        if followup_type == "clarification":
            prompt = f"""
            Based on the previous patent search results below, provide a clear and detailed clarification for this follow-up question: "{query}"
            
            Focus on explaining concepts, terms, or details that might need clarification.
            
            Previous Results:
            {combined_content}
            """
        
        elif followup_type == "expansion":
            prompt = f"""
            Based on the previous patent search results below, expand on the topic with additional relevant information for this question: "{query}"
            
            Provide broader context, related technologies, or industry implications.
            
            Previous Results:
            {combined_content}
            """
        
        elif followup_type == "specific":
            prompt = f"""
            Based on the previous patent search results below, provide specific details requested in this follow-up question: "{query}"
            
            Focus on the particular aspect or component being asked about.
            
            Previous Results:
            {combined_content}
            """
        
        elif followup_type == "application":
            prompt = f"""
            Based on the previous patent search results below, explain the applications, uses, or practical implementations related to this question: "{query}"
            
            Focus on how the technology is or can be used in real-world scenarios.
            
            Previous Results:
            {combined_content}
            """
        
        elif followup_type == "comparison":
            prompt = f"""
            Based on the previous patent search results below, provide comparisons or contrasts as requested in this question: "{query}"
            
            Compare different aspects, technologies, or approaches mentioned in the results.
            
            Previous Results:
            {combined_content}
            """
        
        else:
            prompt = f"""
            Based on the previous patent search results below, answer this follow-up question: "{query}"
            
            Provide a helpful and contextual response using the available information.
            
            Previous Results:
            {combined_content}
            """
        
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        
        if response and hasattr(response, "text"):
            return response.text.strip()
        else:
            return "I couldn't generate a proper response based on the previous context."
    
    except Exception as e:
        print(f"❌ Contextual response error: {e}")
        return "Error generating contextual response based on previous results."

def extract_keywords_from_results(results: List[Dict]) -> List[str]:
    """
    Extract key terms and concepts from search results for better follow-up detection.
    """
    try:
        combined_text = ""
        for result in results:
            combined_text += f"{result.get('title', '')} {result.get('detailed_summary', '')} "
        
        prompt = f"""
        Extract the most important technical terms, concepts, and keywords from this patent content.
        Return only a comma-separated list of single words or short phrases (2-3 words max).
        Focus on technical terms, patent concepts, and key technologies mentioned.
        Limit to 15 most important terms.
        
        Content: {combined_text[:2000]}
        """
        
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        
        if response and hasattr(response, "text"):
            keywords = [kw.strip().lower() for kw in response.text.strip().split(",")]
            return [kw for kw in keywords if kw and len(kw) > 2][:15]
        
        return []
    
    except Exception as e:
        print(f"❌ Keyword extraction error: {e}")
        return []

def is_query_completely_irrelevant(query: str, context_keywords: List[str]) -> bool:
    """
    Check if a follow-up query is completely irrelevant to the previous context.
    """
    try:
        query_lower = query.lower()
        
        # Check for obvious irrelevant topics
        irrelevant_topics = [
            "weather", "sports", "cooking", "movie", "music", "celebrity",
            "politics", "religion", "travel", "shopping", "fashion",
            "dating", "relationship", "game", "joke", "funny"
        ]
        
        if any(topic in query_lower for topic in irrelevant_topics):
            return True
        
        # Check overlap with context keywords
        query_words = set(query_lower.split())
        context_words = set(context_keywords)
        
        # If there's any overlap, it might be relevant
        if context_words.intersection(query_words):
            return False
        
        # Use Gemini for final determination
        prompt = f"""
        Is this query completely irrelevant to patents, intellectual property, or technology?
        
        Query: "{query}"
        Context keywords from previous discussion: {', '.join(context_keywords)}
        
        Answer with only 'yes' if completely irrelevant, or 'no' if it could be related.
        """
        
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        
        if response and hasattr(response, "text"):
            return "yes" in response.text.strip().lower()
        
        return False
    
    except Exception as e:
        print(f"❌ Irrelevance check error: {e}")
        return False