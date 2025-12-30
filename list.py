#find existing models you can use
from google import genai
from pprint import pprint

client = genai.Client(api_key="YOUR_GEMINI_KEY")

for model in client.models.list():
    print("\nMODEL NAME:")
    print(model.name)

    print("FULL MODEL OBJECT:")
    pprint(model.model_dump())
