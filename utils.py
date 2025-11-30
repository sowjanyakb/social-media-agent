import os
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

import openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

PLATFORM_GUIDELINES = {
    "Instagram": {"max_len": 2200, "notes": "Focus on visuals, include hashtags"},
    "LinkedIn": {"max_len": 1300, "notes": "Professional, value-first"},
    "X/Twitter": {"max_len": 280, "notes": "Concise, hook-driven"},
    "Facebook": {"max_len": 63206, "notes": "Conversational, community-focused"},
    "TikTok": {"max_len": 150, "notes": "Short caption + CTA, pairing with video idea"}
}

def _build_prompt(topic: str, brand_voice: str, platform: str, tone: str, variation_idx: int) -> str:
    """
    Build a platform-aware prompt that asks the LLM to return JSON.
    """
    guidelines = PLATFORM_GUIDELINES.get(platform, {})
    prompt = f"""
You are a professional social media copywriter.

Topic: {topic}
Brand voice / audience: {brand_voice}
Platform: {platform} (guidelines: {guidelines.get('notes','')}, max length {guidelines.get('max_len','N/A')})
Tone: {tone}

Task:
- Generate ONE caption optimized for the platform.
- Provide suggested hashtags (comma-separated).
- Provide a short CTA (one sentence) if applicable.
- Keep the caption under {guidelines.get('max_len','280')} characters.

Output format (STRICT JSON):
{{
  "caption": "...",
  "hashtags": "...",   # comma-separated
  "cta": "..."
}}

Variation: {variation_idx}
"""
    return prompt.strip()

def _call_openai(prompt: str, max_tokens: int = 150) -> str:
    """
    Call the OpenAI ChatCompletion endpoint. Returns the assistant's text.
    """
    if not OPENAI_API_KEY:
        # Helpful fallback message for debugging (won't leak keys)
        return '{"caption":"(error) OPENAI_API_KEY not set","hashtags":"","cta":""}'

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        # Return a JSON-like error string so parsing downstream doesn't crash
        return '{"caption":"(error) Could not generate content - ' + str(e).replace("\"","'") + '","hashtags":"","cta":""}'

import json
def _parse_response_to_struct(resp_text: str) -> Dict[str, str]:
    """
    Try to parse the LLM response as JSON. If that fails, apply heuristics.
    Returns a dict with keys: caption, hashtags, cta
    """
    # First, try to find a JSON object inside the response (robust to extra text)
    try:
        # If the model returned extra text, attempt to extract the first JSON block
        start = resp_text.find('{')
        end = resp_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = resp_text[start:end+1]
            obj = json.loads(candidate)
        else:
            # fallback: direct parse (may raise)
            obj = json.loads(resp_text)
        return {
            "caption": obj.get("caption", "").strip(),
            "hashtags": obj.get("hashtags", "").strip(),
            "cta": obj.get("cta", "").strip()
        }
    except Exception:
        # Heuristic fallback parsing
        lines = [l.strip() for l in resp_text.splitlines() if l.strip()]
        caption = lines[0] if lines else ""
        hashtags = ""
        cta = ""
        for l in lines:
            if "#" in l or "hashtag" in l.lower():
                hashtags += (l + " ")
            # simple CTA detection
            if l.lower().startswith("cta") or "call to action" in l.lower() or "visit" in l.lower() or "check" in l.lower() or "register" in l.lower():
                cta += (l + " ")
        return {"caption": caption, "hashtags": hashtags.strip(), "cta": cta.strip()}

def generate_social_posts(topic: str, brand_voice: str, platforms: List[str], tone: str, n_variations: int = 2) -> Dict[str, List[Dict]]:
    """
    Generate social post variations for each requested platform.
    Returns dict: { platform_name: [ {caption, hashtags, cta}, ... ] }
    """
    results: Dict[str, List[Dict]] = {}
    for platform in platforms:
        items: List[Dict] = []
        for i in range(n_variations):
            prompt = _build_prompt(topic, brand_voice, platform, tone, variation_idx=i+1)
            resp_text = _call_openai(prompt)
            parsed = _parse_response_to_struct(resp_text)
            items.append(parsed)
        results[platform] = items
    return results

# Utility to create a CSV bytes payload for Streamlit download_button
import io, csv
def export_calendar_csv(calendar: List[Dict]) -> bytes:
    """
    Convert a calendar list of dicts to CSV bytes. Each row should have: date, platform, caption
    """
    output = io.StringIO()
    fieldnames = ["date", "platform", "caption"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in calendar:
        # Ensure keys exist
        writer.writerow({
            "date": row.get("date", ""),
            "platform": row.get("platform", ""),
            "caption": row.get("caption", "")
        })
    return output.getvalue().encode("utf-8")
