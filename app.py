import os
import streamlit as st
from dotenv import load_dotenv
from utils import generate_social_posts, export_calendar_csv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Social Media Agent", layout="wide")
st.title("📣 Social Media Agent")

with st.sidebar:
    st.header("Settings")
    model = st.selectbox("Model (Local/Provider)", ["OpenAI (recommended)"])
    tone_default = st.selectbox("Default Tone", ["Professional", "Casual", "Funny", "Inspirational"])
    st.markdown("**Tips:** Provide a short brand voice + target audience for better results.")

# Input area
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

if generate:
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Generating content..."):
            results = generate_social_posts(topic=topic, brand_voice=brand_voice, platforms=platforms, tone=tone, n_variations=num_variations)
            st.success("Done — review below!")
        # Display results
        for platform, items in results.items():
            st.markdown(f"### {platform}")
            for i, item in enumerate(items, start=1):
                st.markdown(f"**Variation {i}**")
                st.write(item.get("caption",""))
                if item.get("hashtags"):
                    st.markdown(f"**Hashtags:** {item.get('hashtags')}")
                if item.get("cta"):
                    st.markdown(f"**CTA:** {item.get('cta')}")
                st.markdown("---")

        # Calendar generation
        st.markdown("### Content Calendar")
        if st.button("Generate 7-day content calendar"):
            with st.spinner("Building calendar..."):
                calendar = []
                from datetime import datetime, timedelta
                start = datetime.today()
                # simple round-robin across platforms
                for i in range(7):
                    date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
                    platform = platforms[i % len(platforms)] if platforms else "Instagram"
                    items = results.get(platform, [])
                    caption = items[i % len(items)].get("caption","") if items else ""
                    calendar.append({"date": date, "platform": platform, "caption": caption})
                st.table(calendar)
                csv_bytes = export_calendar_csv(calendar)
                st.download_button("Download CSV", data=csv_bytes, file_name="content_calendar.csv", mime="text/csv")
