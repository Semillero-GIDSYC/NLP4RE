import sys
sys.path.append('/app/app')
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="google/gemma-3-4b:2",
    openai_api_base="http://host.docker.internal:1234/v1/",
    openai_api_key="lm-studio"
)

try:
    res = llm.invoke("Hola mundo")
    print("Success. Content:", res.content)
except Exception as e:
    import traceback
    traceback.print_exc()
