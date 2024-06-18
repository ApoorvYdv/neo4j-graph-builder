from app.utils.llm.gemini import Gemini
from app.utils.llm.groq import Groq
from app.utils.llm.ollama import OllamaLLM
from app.utils.llm.openai import OpenAI


class LLMFactory(object):
    def __init__(self):
        pass

    def get_llm_class(self, model_name):
        default_class = {
            "openai": OpenAI,
            "gemini": Gemini,
            "groq": Groq,
            "ollama": OllamaLLM,
        }
        return default_class.get(model_name)

    def build(self, model_name):
        llm_class = self.get_llm_class(model_name)
        return llm_class()
