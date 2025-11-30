# utils.py
import os
from typing import List, Dict
import json
import io, csv
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Use OpenAI client v1+
try:
    from openai import OpenAI
    client = OpenAI()  # reads OPENAI_API_KEY from env by default
except Exception:
    client = None

PLATFORM_GUIDELINES = {
    "Instagram": {"max_len": 2200, "notes": "Focus on visuals, include hashtags"},
    "LinkedIn": {"max_len": 1300, "notes": "Professional, value-first"},
    "X/Twitter": {"max_len": 280, "notes": "Concise, engaging hooks"},
    "Facebook": {"max_len": 63206, "notes": "Conversational, community-focused"},
    "TikTok": {"max_len": 150, "notes": "Short, punchy, CTA-based"}
}

def _build_prompt(topic: str, brand_voice: str, platform: str, tone: str, variation_idx: int) -> str:
    guidelines = PLATFORM_GUIDELINES.get(platform, {})
    prompt = f"""
You are a professional social media copywriter.

Topic: {topic}
Brand Voice: {brand_voice}
Platform: {platform} (Notes: {guidelines.get('notes', '')}, Max length: {guidelines.get('max_len', 'N/A')})
Tone: {tone}

Task:
- Generate ONE caption optimized for the platform
- Add suggested hashtags (comma-separated)
- Add one CTA sentence (if applicable)
- Keep caption under {guidelines.get('max_len', 200)} characters

Output in STRICT JSON format (only JSON):
{{
  "caption": "",
  "hashtags": "",
  "cta": ""
}}

Variation: {variation_idx}
"""
    return prompt.strip()

def _call_openai(prompt: str, max_tokens: int = 150) -> str:
    """
    New OpenAI client usage (openai>=1.0.0).
    Tries multiple models in order and logs failures.
    Returns the raw assistant text (string).
    """
    if not OPENAI_API_KEY:
        return '{"caption":"(error) OPENAI_API_KEY not set","hashtags":"","cta":""}'

    if client is None:
        return '{"caption":"(error) OpenAI client not available","hashtags":"","cta":""}'

    models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    last_error = None

    for model_name in models:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            # resp.choices[0].message.content is typical
            try:
                return resp.choices[0].message.content
            except Exception:
                # some client shapes may put text differently
                try:
                    return resp.choices[0].text
                except Exception:
                    return str(resp)
        except Exception as e:
            last_error = e
            try:
                with open("openai_error.log", "a", encoding="utf-8") as fh:
                    import traceback
                    fh.write(f"\n=== ERROR model={model_name} ===\n")
                    fh.write(traceback.format_exc())
            except Exception:
                pass
            continue

    msg = str(last_error).replace('"', "'") if last_error else "unknown error"
    return '{"caption":"(error) Could not generate content - ' + msg + '","hashtags":"","cta":""}'

def _parse_response_to_struct(resp_text: str) -> Dict[str, str]:
    """
    Extract JSON block from model output; fallback to heuristics.
    """
    try:
        start = resp_text.find('{')
        end = resp_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            block = resp_text[start:end+1]
            obj = json.loads(block)
            return {
                "caption": obj.get("caption", "").strip(),
                "hashtags": obj.get("hashtags", "").strip(),
                "cta": obj.get("cta", "").strip()
            }
    except Exception:
        pass

    # fallback heuristics
    lines = [l.strip() for l in resp_text.splitlines() if l.strip()]
    caption = lines[0] if lines else ""
    hashtags = ""
    cta = ""
    for l in lines:
        if "#" in l or "hashtag" in l.lower():
            hashtags += (l + " ")
        if l.lower().startswith("cta") or "call to action" in l.lower() or any(k in l.lower() for k in ["visit", "check", "register"]):
            cta += (l + " ")
    return {"caption": caption, "hashtags": hashtags.strip(), "cta": cta.strip()}

def generate_social_posts(topic: str, brand_voice: str, platforms: List[str], tone: str, n_variations: int = 2) -> Dict[str, List[Dict]]:
    results: Dict[str, List[Dict]] = {}
    for platform in platforms:
        items: List[Dict] = []
        for i in range(n_variations):
            prompt = _build_prompt(topic, brand_voice, platform, tone, variation_idx=i+1)
            raw = _call_openai(prompt)
            parsed = _parse_response_to_struct(raw)
            items.append(parsed)
        results[platform] = items
    return results

def export_calendar_csv(calendar: List[Dict]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "platform", "caption"])
    writer.writeheader()
    for row in calendar:
        writer.writerow({
            "date": row.get("date", ""),
            "platform": row.get("platform", ""),
            "caption": row.get("caption", "")
        })
    return output.getvalue().encode("utf-8")
