# app.py
import os
import streamlit as st
from dotenv import load_dotenv
from utils import generate_social_posts, export_calendar_csv

load_dotenv()
st.set_page_config(page_title="Social Media Agent", layout="wide")
st.title("📣 Social Media Agent")

with st.sidebar:
    st.header("Settings")
    model_note = st.info("Uses OpenAI (gpt-4o-mini recommended) with fallbacks. Make sure OPENAI_API_KEY is set in .env")
    tone_default = st.selectbox("Default Tone", ["Professional", "Casual", "Funny", "Inspirational"])
    st.markdown("**Tips:** Provide a short brand voice + target audience for better results.")

st.subheader("Create social content")
col1, col2 = st.columns([3,1])
with col1:
    topic = st.text_input("Topic / Campaign (e.g., 'New feature X launch')", "")
    brand_voice = st.text_input("Brand voice / Target audience (optional)", "Friendly, startup founders")
    platforms = st.multiselect("Platforms", ["Instagram", "LinkedIn", "X/Twitter", "Facebook", "TikTok"], default=["Instagram","LinkedIn"])
    tone = st.selectbox("Tone", ["Professional", "Casual", "Funny", "Inspirational"], index=["Professional","Casual","Funny","Inspirational"].index(tone_default))
    num_variations = st.slider("Variations per platform (A/B)", 1, 3, 2)
    generate = st.button("Generate posts")

with col2:
    st.markdown("## Quick examples")
    st.markdown("- Topic: `New AI tool launch`")
    st.markdown("- Brand voice: `Helpful, concise, developer-focused`")
    st.markdown("- Platforms: `LinkedIn, X/Twitter`")

def is_error_entry(entry: dict) -> bool:
    cap = entry.get("caption","")
    return cap.startswith("(error)")

if generate:
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Generating content..."):
            try:
                results = generate_social_posts(topic=topic, brand_voice=brand_voice, platforms=platforms, tone=tone, n_variations=num_variations)
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                results = {}

        if not results:
            st.error("No results returned. Check openai_error.log or your API key.")
        else:
            any_error = False
            for platform, items in results.items():
                st.markdown(f"### {platform}")
                for i, item in enumerate(items, start=1):
                    st.markdown(f"**Variation {i}**")
                    caption = item.get("caption","")
                    hashtags = item.get("hashtags","")
                    cta = item.get("cta","")
                    if caption and caption.startswith("(error)"):
                        any_error = True
                        st.error(caption)
                    else:
                        st.write(caption)
                        if hashtags:
                            st.markdown(f"**Hashtags:** {hashtags}")
                        if cta:
                            st.markdown(f"**CTA:** {cta}")
                    st.markdown("---")

            if any_error:
                st.info("If you see errors, check openai_error.log in project folder or ensure OPENAI_API_KEY is valid.")
            # Calendar generation
            st.markdown("### Content Calendar")
            if st.button("Generate 7-day content calendar"):
                with st.spinner("Building calendar..."):
                    from datetime import datetime, timedelta
                    calendar = []
                    start = datetime.today()
                    for i in range(7):
                        date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
                        # round-robin platform + variation pick
                        if platforms:
                            platform = platforms[i % len(platforms)]
                            items = results.get(platform, [])
                            caption = items[i % len(items)].get("caption","") if items else ""
                        else:
                            platform = "Instagram"
                            caption = ""
                        calendar.append({"date": date, "platform": platform, "caption": caption})
                    st.table(calendar)
                    csv_bytes = export_calendar_csv(calendar)
                    st.download_button("Download CSV", data=csv_bytes, file_name="content_calendar.csv", mime="text/csv")
