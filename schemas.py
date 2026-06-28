from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class AnalysisResult(BaseModel):
    prompt: str
    is_injection: bool
    label: str
    attack_category: str
    confidence: float