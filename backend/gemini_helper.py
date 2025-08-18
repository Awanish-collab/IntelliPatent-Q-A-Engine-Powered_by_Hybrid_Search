# backend/gemini_helper.py
import os
import google.generativeai as genai_1
from dotenv import load_dotenv
from google.genai import types
from google import genai

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
genai_1.configure(api_key=api_key)

gemini_model = genai_1.GenerativeModel("gemini-2.5-flash-lite")

generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2500,
}

# ---------------------- Embeddings ----------------------
def generate_dense_embedding(text):
    """Generate dense embeddings for a given text using Gemini."""
    try:
        if not text or not text.strip():
            return None
        client = genai.Client(api_key=api_key)
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"❌ Dense Embedding Error: {e}")
        return None


# ---------------------- Summary ----------------------
def generate_summary(query, result):
    try:
        prompt = f"""
        You are an expert patent analyst. Based on the user's query '{query}', provide a comprehensive and structured summary of the following patent details.

        Your summary should be broken down into the following sections:

        1. **Invention Overview**
        2. **Key Features & Components**
        3. **Claims**
        4. **Applications**

        Only include information present in the given data. Do not make up facts.

        Patent details from DB:
        {result}
        """
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Summary Generation Error: {e}")
        return ""


# ---------------------- Classification ----------------------
def classify_query_type(query: str) -> str:
    """Classify query as 'irrelevant', 'generic', or 'specific'."""
    prompt = f"""
    You are a query classifier for a Patent Q&A system.

    Categories:
    - 'irrelevant' → Query is NOT related to patents, inventions, or intellectual property.
    - 'generic' → Query IS related to patents but is broad/general.
    - 'specific' → Query is related to patents and is specific enough that it might match a document in a patent database.

    Respond with exactly one word: irrelevant, generic, or specific.

    Query: {query}
    """
    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        if not response or not hasattr(response, "text"):
            return "irrelevant"
        category = response.text.strip().lower()
        if category not in ["irrelevant", "generic", "specific"]:
            return "irrelevant"
        return category
    except Exception as e:
        print(f"❌ Gemini classification error: {e}")
        return "irrelevant"


# ---------------------- Generic Answer ----------------------
def generate_generic_answer(query: str) -> str:
    """Generate an answer for generic patent-related queries directly using Gemini."""
    try:
        prompt = f"""
        You are an expert in intellectual property law and patents.
        Answer the following general question in a clear, concise, and accurate manner:

        Question: {query}

        Provide structured and informative content without unnecessary details.
        """
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini generic answer error: {e}")
        return "Unable to generate a response."




'''# backend/gemini_helper.py
import os
import google.generativeai as genai_1
from dotenv import load_dotenv
from google.genai import types
from google import genai

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
genai_1.configure(api_key=api_key)

gemini_model = genai_1.GenerativeModel("gemini-2.5-flash-lite")

generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2500, # Set a limit for the summary length
}

def generate_dense_embedding(text):
    try:
        client = genai.Client(api_key=api_key)

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"❌ Dense Embedding Error: {e}")
        return None

def generate_summary(query, result):
    try:
        print(f"Combined Text Length: {len(result)}")
        prompt = f"""
        You are an expert patent analyst. Based on the user's query '{query}', provide a comprehensive and structured summary of the following patent details.

        Your summary should be broken down into the following sections and should capture all important points from the retrieved data:

        1.  **Invention Overview:** A brief description of the invention's purpose and problem it solves.
        2.  **Key Features & Components:** A list of the main technical features and components of the patent.
        3.  **Claims:** A summary of the primary claims and what the patent protects.
        4.  **Applications:** Potential uses or industries where the invention could be applied.

        Do not include any introductory phrases, greetings, or unnecessary information. Focus exclusively on the content of the summary.

        Here is the patent details retrieved from the vector database:
        {result}
        """
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Summary Generation Error: {e}")
        return ""
    
def is_query_relevant(query: str) -> bool:
    """Check if query is relevant to patents, inventions, or IP."""
    prompt = f"""
    Determine if the following query is relevant to patents, inventions, intellectual property, 
    or technology innovations. Respond with only 'yes' or 'no'.

    Query: {query}
    """

    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )

        if not response or not hasattr(response, "text"):
            return False

        answer = response.text.strip().lower()
        return answer.startswith("y")  # yes → True, no → False
    except Exception as e:
        print(f"❌ Gemini relevance check error: {e}")
        return False'''
    
    
'''text = """The patent US1234567B2, titled "Method for Autonomous Drone Navigation", was invented by Jane Smith and Robert Johnson and is assigned to SkyTech Innovations Inc.. It was filed on March 12, 2020 and officially issued on October 5, 2022. The invention introduces an AI-powered navigation system that enables drones to detect and avoid obstacles in real time, ensuring safer and more efficient flight paths. The patent contains 12 claims, which cover various aspects including path planning algorithms, collision avoidance mechanisms, and adaptive route optimization techniques. The detailed description outlines the integration of hardware components with advanced software models, the training of the machine learning system using large datasets, and the use of sensor fusion to combine visual, infrared, and GPS data for precise navigation. This innovation is designed to work across multiple drone platforms, enhancing their autonomous capabilities for applications in delivery, surveillance, and environmental monitoring. The patent is currently granted and active, with protection extending until 2042."""

summary = generate_summary(text)
print(summary)

print()

dense_embedding = generate_dense_embedding(text)
print(dense_embedding)
print(len(dense_embedding))'''



'''# backend/gemini_helper.py
import os
import google.generativeai as genai_1
from dotenv import load_dotenv
from google.genai import types
from google import genai

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
genai_1.configure(api_key=api_key)

gemini_model = genai_1.GenerativeModel("gemini-2.5-flash-lite")

generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2500, # Set a limit for the summary length
}

def generate_dense_embedding(text):
    try:
        client = genai.Client(api_key=api_key)

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"❌ Dense Embedding Error: {e}")
        return None

def generate_summary(query, result):
    try:
        print(f"Combined Text Length: {len(result)}")
        prompt = f"""
        You are an expert patent analyst. Based on the user's query '{query}', provide a comprehensive and structured summary of the following patent details.

        Your summary should be broken down into the following sections and should capture all important points from the retrieved data:

        1.  **Invention Overview:** A brief description of the invention's purpose and problem it solves.
        2.  **Key Features & Components:** A list of the main technical features and components of the patent.
        3.  **Claims:** A summary of the primary claims and what the patent protects.
        4.  **Applications:** Potential uses or industries where the invention could be applied.

        Do not include any introductory phrases, greetings, or unnecessary information. Focus exclusively on the content of the summary.

        Here is the patent details retrieved from the vector database:
        {result}
        """
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Summary Generation Error: {e}")
        return ""
    
def is_query_relevant(query: str) -> bool:
    """Check if query is relevant to patents, inventions, or IP."""
    prompt = f"""
    Determine if the following query is relevant to patents, inventions, intellectual property, 
    or technology innovations. Respond with only 'yes' or 'no'.

    Query: {query}
    """

    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )

        if not response or not hasattr(response, "text"):
            return False

        answer = response.text.strip().lower()
        return answer.startswith("y")  # yes → True, no → False
    except Exception as e:
        print(f"❌ Gemini relevance check error: {e}")
        return False'''
    
    
'''text = """The patent US1234567B2, titled "Method for Autonomous Drone Navigation", was invented by Jane Smith and Robert Johnson and is assigned to SkyTech Innovations Inc.. It was filed on March 12, 2020 and officially issued on October 5, 2022. The invention introduces an AI-powered navigation system that enables drones to detect and avoid obstacles in real time, ensuring safer and more efficient flight paths. The patent contains 12 claims, which cover various aspects including path planning algorithms, collision avoidance mechanisms, and adaptive route optimization techniques. The detailed description outlines the integration of hardware components with advanced software models, the training of the machine learning system using large datasets, and the use of sensor fusion to combine visual, infrared, and GPS data for precise navigation. This innovation is designed to work across multiple drone platforms, enhancing their autonomous capabilities for applications in delivery, surveillance, and environmental monitoring. The patent is currently granted and active, with protection extending until 2042."""

summary = generate_summary(text)
print(summary)

print()

dense_embedding = generate_dense_embedding(text)
print(dense_embedding)
print(len(dense_embedding))'''
