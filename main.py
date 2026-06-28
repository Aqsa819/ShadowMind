from fastapi import FastAPI, HTTPException
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from schemas import PromptRequest, AnalysisResult
import torch
import uvicorn

app = FastAPI(title="ShadowMind API", description="LLM Prompt Injection Detector")

model = None
tokenizer = None
MODEL_PATH = r"C:\Users\Azhar computer\ShadowMind\shadowmind_final"

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    print("Model load ho raha hai...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    print("Model ready!")

def get_attack_category(label: str, prompt: str) -> str:
    if label == "BENIGN":
        return "none"
    prompt_lower = prompt.lower()
    if "forget" in prompt_lower or "ignore" in prompt_lower:
        return "direct_jailbreak"
    elif "you are now" in prompt_lower or "you are a" in prompt_lower:
        return "role_override"
    elif "system prompt" in prompt_lower or "instructions" in prompt_lower:
        return "goal_hijacking"
    else:
        return "indirect_injection"

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_prompt(request: PromptRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt empty hai")
    if len(request.prompt) > 1000:
        raise HTTPException(status_code=400, detail="Prompt bohot lamba hai")

    inputs = tokenizer(
        request.prompt,
        return_tensors="pt",
        truncation=True,
        max_length=128,
        padding="max_length"
    )
    inputs = {k: v for k, v in inputs.items() if k != "token_type_ids"}

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=-1)
    predicted_class = torch.argmax(probs).item()
    confidence = probs[0][predicted_class].item()

    is_injection = predicted_class == 1
    label = "INJECTION" if is_injection else "BENIGN"

    return AnalysisResult(
        prompt=request.prompt,
        is_injection=is_injection,
        label=label,
        attack_category=get_attack_category(label, request.prompt),
        confidence=round(confidence, 4)
    )

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)