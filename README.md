# Social Media Agent

**One-line:** Generate platform-specific social posts, captions, hashtags and a 7-day content calendar from a topic, audience, and tone.

## Demo
- Streamlit demo UI: pick platform(s), enter topic + tone, generate posts.
- Hosted demo link: _(optional, add after deployment)_

## Features
- Generate content for multiple platforms (Instagram, LinkedIn, X/Twitter, Facebook, TikTok caption ideas).
- Choose tone (Professional, Casual, Funny, Inspirational).
- Produce variations (A/B captions) and suggested hashtags.
- Create a short content calendar (7 days) with post dates & captions.
- Export to CSV for easy posting.

## Tech stack
- Python 3.10+
- Streamlit (UI)
- OpenAI (or any LLM via LangChain simple wrapper)
- (Optional) image generation prompt helper

## Quick start (local)
1. Clone:
   ```bash
   git clone <repo-url>
   cd social-media-agent
   ```
2. Create venv & install:
   ```bash
   python -m venv venv
   source venv/bin/activate    # macOS/Linux
   venv\\Scripts\\activate     # Windows
   pip install -r requirements.txt
   ```
3. Create `.env` (or set env var):
   ```
   OPENAI_API_KEY=sk-...
   ```
4. Run:
   ```bash
   streamlit run app.py
   ```

## Usage flow
1. Enter a **Topic** and optional **Brand Voice / Target Audience**.
2. Select platforms & tone.
3. Click **Generate** — outputs appear grouped by platform with variations and hashtag suggestions.
4. Optionally click **Generate Calendar** to produce a 7-day plan and download CSV.

## Limitations
- Output quality depends on the LLM and prompt design.
- Platform trends / hashtags may be stale—does not auto-check live trends.
- Not a replacement for human moderation.

## Improvements
- Add scheduling via Buffer/Meta/LinkedIn APIs.
- Integrate live hashtag trend lookup.
- Add image generation & auto-layout for posts.
- Add analytics + A/B performance tracking.

## License
MIT
