from groq import Groq

GROQ_API_KEY = "gsk_your_key_here"   # <-- paste your real key here

client = Groq(api_key=GROQ_API_KEY)

print("Models available to your key:\n")
for m in client.models.list().data:
    print(m.id)
