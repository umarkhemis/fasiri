# Build a Multilingual Chatbot

```python
from fasiri import Fasiri

client = Fasiri(api_key="fsri_...")

def chat(user_message: str, user_language: str) -> str:
    # 1. Translate user message to English
    if user_language != "en":
        en_input = client.translate(user_message, target="en").translated_text
    else:
        en_input = user_message

    # 2. Process in English (your LLM/logic here)
    en_response = f"You said: {en_input}"

    # 3. Translate response back to user's language
    if user_language != "en":
        return client.translate(en_response, target=user_language).translated_text
    return en_response

# Luganda user
print(chat("Nkwagala obuyambi", user_language="lug"))

# Yoruba user
print(chat("Mo nilo iranlowo", user_language="yo"))
```
