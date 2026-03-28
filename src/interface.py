import streamlit as st
import pandas as pd
import feedparser
import os
import time
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- 1. INITIALIZATION ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="KUSH PADDOCK COMMAND", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #111827; }
    h1, h2, h3, h4 { color: #111827 !important; font-weight: 800 !important; }
    
    /* --- BASE DESKTOP CSS --- */
    .countdown-timer { font-family: 'Courier New', monospace; font-size: 80px; font-weight: 900; color: #e10600; text-align: center; margin-bottom: -10px; line-height: 1; }
    .countdown-labels { text-align: center; color: #6b7280; font-weight: 700; font-size: 14px; letter-spacing: 12px; margin-bottom: 20px; margin-left: 12px; }
    .race-title { text-align: center; color: #111827; font-weight: 900; font-size: 24px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; }
    .live-badge { display: inline-block; background: #e10600; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 800; font-size: 14px; animation: pulse 1.5s infinite; vertical-align: middle; margin-right: 10px;}
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    .clean-card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    
    .track-wrapper { position: relative; width: 100%; border-radius: 15px; overflow: hidden; background: #0f172a; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border: 2px solid #e5e7eb; }
    .driver-dot { position: absolute; width: 18px; height: 18px; border-radius: 50%; border: 2px solid white; z-index: 10; font-size: 10px; color: white; text-align: center; line-height: 14px; font-weight: 900; box-shadow: 0 0 10px rgba(0,0,0,0.5); transform: translate(-50%, -50%); transition: all 1s linear; }
    
    .news-card { padding: 15px; border-radius: 10px; background: white; border: 1px solid #e2e8f0; height: 100%; }
    .news-card a { text-decoration: none; color: #1e293b; font-weight: 700; font-size: 14px; }
    .news-card a:hover { color: #e10600; }
    
    .block-container { padding-top: 1.5rem; }

    /* --- MOBILE RESPONSIVE OVERRIDES --- */
    @media (max-width: 768px) {
        .countdown-timer { font-size: 35px !important; margin-bottom: 0px !important; }
        .countdown-labels { font-size: 10px !important; letter-spacing: 4px !important; margin-left: 0px !important; }
        .race-title { font-size: 16px !important; }
        .driver-dot { width: 12px !important; height: 12px !important; font-size: 7px !important; line-height: 9px !important; border: 1px solid white !important; }
        .news-card { margin-bottom: 10px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. THE 2026 CALENDAR ENGINE ---
F1_CALENDAR = [
    {"name": "Australian Grand Prix", "date": "2026-03-08"},
    {"name": "Chinese Grand Prix", "date": "2026-03-15"},
    {"name": "Japanese Grand Prix", "date": "2026-03-29"},
    {"name": "Bahrain Grand Prix", "date": "2026-04-12"},
    {"name": "Saudi Arabian Grand Prix", "date": "2026-04-19"},
    {"name": "Miami Grand Prix", "date": "2026-05-03"},
    {"name": "Canadian Grand Prix", "date": "2026-05-24"},
    {"name": "Monaco Grand Prix", "date": "2026-06-07"},
    {"name": "Spanish Grand Prix", "date": "2026-06-14"},
    {"name": "Austrian Grand Prix", "date": "2026-06-28"},
    {"name": "British Grand Prix", "date": "2026-07-05"},
    {"name": "Belgian Grand Prix", "date": "2026-07-19"},
    {"name": "Hungarian Grand Prix", "date": "2026-07-26"},
    {"name": "Dutch Grand Prix", "date": "2026-08-23"},
    {"name": "Italian Grand Prix", "date": "2026-09-06"},
    {"name": "Madrid Grand Prix", "date": "2026-09-13"},
    {"name": "Azerbaijan Grand Prix", "date": "2026-09-26"},
    {"name": "Singapore Grand Prix", "date": "2026-10-11"},
    {"name": "United States Grand Prix", "date": "2026-10-25"},
    {"name": "Mexico City Grand Prix", "date": "2026-11-01"},
    {"name": "São Paulo Grand Prix", "date": "2026-11-08"},
    {"name": "Las Vegas Grand Prix", "date": "2026-11-21"},
    {"name": "Qatar Grand Prix", "date": "2026-11-29"},
    {"name": "Abu Dhabi Grand Prix", "date": "2026-12-06"}
]

def get_race_status():
    now = datetime.now()
    for race in F1_CALENDAR:
        race_time = datetime.strptime(race["date"] + " 15:00:00", "%Y-%m-%d %H:%M:%S")
        if race_time > now:
            time_left = race_time - now
            if time_left.days == 0 and time_left.seconds < 10800:
                return {"status": "LIVE", "name": race["name"]}
            else:
                d = time_left.days
                h, rem = divmod(time_left.seconds, 3600)
                m, s = divmod(rem, 60)
                return {"status": "COUNTDOWN", "name": race["name"], "timer": f"{d:02d} : {h:02d} : {m:02d} : {s:02d}"}
    return {"status": "SEASON_OVER", "name": "2027 Season", "timer": "00 : 00 : 00 : 00"}

status = get_race_status()

# --- 3. HTML TRACK SIMULATOR (Paddock Standby) ---
track_points = [[75, 70], [88, 85], [75, 50], [60, 60], [30, 45], [10, 30], [40, 60], [60, 75], [75, 70]]

def get_simulated_html_positions():
    current_time = time.time()
    num_points = len(track_points) - 1
    drivers_data = []
    
    grid = [
        {"pos": 1, "name": "K. Antonelli", "short": "ANT", "hex": "#00d2be", "speed": 0.30, "offset": 0.0},
        {"pos": 2, "name": "G. Russell", "short": "RUS", "hex": "#00d2be", "speed": 0.29, "offset": 0.2},
        {"pos": 3, "name": "C. Leclerc", "short": "LEC", "hex": "#ef1a2d", "speed": 0.28, "offset": 0.5},
        {"pos": 4, "name": "O. Piastri", "short": "PIA", "hex": "#ff8700", "speed": 0.28, "offset": 0.7},
        {"pos": 5, "name": "L. Hamilton", "short": "HAM", "hex": "#ef1a2d", "speed": 0.27, "offset": 1.1},
        {"pos": 6, "name": "M. Verstappen", "short": "VER", "hex": "#0600ef", "speed": 0.26, "offset": 1.5},
    ]
    
    for d in grid:
        progress = (current_time * d["speed"] + d["offset"]) % num_points
        idx = int(progress)
        fraction = progress - idx
        p1 = track_points[idx]
        p2 = track_points[idx + 1]
        d["x"] = p1[0] + (p2[0] - p1[0]) * fraction
        d["y"] = p1[1] + (p2[1] - p1[1]) * fraction
        drivers_data.append(d)
        
    return drivers_data

live_drivers = get_simulated_html_positions()

# --- 4. TOP NAV ---
st.markdown("<h3 style='text-align: center; color: #e10600; letter-spacing: 2px;'>🏎️ VIP ACCESS: WELCOME FANS</h3>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏁 RACE CONTROL", "🔮 KUSH'S PREDICTIONS"])

with tab1:
    col_chat, col_main, col_standings = st.columns([1.2, 2.5, 1])
    
    with col_chat:
        st.subheader("🤖 Live Assistant")
        st.markdown("<p style='font-size: 13px; color: #6b7280; font-style: italic; margin-bottom: 15px;'>Welcome to the paddock chat window. You can use this assistance to ask any questions about the race, season, drivers, anything your F1 heart desires.</p>", unsafe_allow_html=True)
        
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]): st.write(msg["content"])
                
        if p := st.chat_input("Ask the strategist..."):
            st.session_state.chat_history.append({"role": "user", "content": p})
            st.rerun() 
        
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        ans = client.models.generate_content(
                            model='gemini-3.1-pro-preview',
                            contents=f"F1 Race Engineer. 2026 season context. Answer briefly: {st.session_state.chat_history[-1]['content']}",
                            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearchRetrieval())])
                        ).text
                        st.write(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_main:
        if status["status"] == "COUNTDOWN":
            st.markdown(f'<p class="race-title">NEXT RACE: {status["name"]}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="countdown-timer">{status["timer"]}</p>', unsafe_allow_html=True)
            st.markdown('<p class="countdown-labels">DAYS &nbsp; HRS &nbsp; MINS &nbsp; SECS</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="race-title"><span class="live-badge">LIVE</span>{status["name"]}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="countdown-timer">{datetime.now().strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)
            st.markdown('<p class="countdown-labels">SESSION CLOCK</p>', unsafe_allow_html=True)
            
        map_html = '<div class="track-wrapper">'
        map_html += '<img src="https://media.formula1.com/image/upload/content/dam/fom-website/2018-redesign-assets/Circuit%20maps%2016x9/Japan_Circuit.png" style="width: 100%; display: block;">'
        
        for d in live_drivers:
            map_html += f'<div class="driver-dot" style="background: {d["hex"]}; top: {d["y"]}%; left: {d["x"]}%;">{d["short"]}</div>'
            
        map_html += '</div>'
        if status["status"] == "COUNTDOWN":
            st.caption("🏎️ Paddock Standby Mode: Simulating telemetry from previous session.")
        st.markdown(map_html, unsafe_allow_html=True)

    with col_standings:
        st.subheader("🏆 Grid Order")
        for d in live_drivers:
            st.markdown(f"""
            <div style='padding:12px; background:#f9fafb; margin-bottom:8px; border-radius:8px; border-left:6px solid {d['hex']}; border: 1px solid #e5e7eb;'>
                <span style='font-weight:900; color:#9ca3af; margin-right:8px;'>P{d['pos']}</span> 
                <span style='font-weight:700; color:#111827;'>{d['name']}</span>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("📰 Paddock News")
    news_cols = st.columns(4)
    feed = feedparser.parse("https://www.autosport.com/rss/f1/news")
    
    for i, col in enumerate(news_cols):
        if i < len(feed.entries):
            entry = feed.entries[i]
            with col:
                st.markdown(f'''
                <div class="news-card">
                    <a href="{entry.link}" target="_blank">{entry.title}</a>
                    <br><small style="color:#94a3b8; margin-top:10px; display:block;">{entry.published[:16]}</small>
                </div>
                ''', unsafe_allow_html=True)

with tab2:
    st.subheader("🔮 Full Grid Win Probability")
    st.write("Calculated based on 2026 performance trends.")
    st.write("---")
    probs = [("K. Antonelli", "Mercedes", 45), ("G. Russell", "Mercedes", 25), ("C. Leclerc", "Ferrari", 15), 
             ("O. Piastri", "McLaren", 8), ("L. Hamilton", "Ferrari", 5), ("M. Verstappen", "Red Bull", 2)]
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        for name, team, p in probs[:3]:
            st.markdown(f"**{name} ({team})**")
            st.progress(p / 100, text=f"{p}%")
            st.write("")
    with col_p2:
        for name, team, p in probs[3:]:
            st.markdown(f"**{name} ({team})**")
            st.progress(p / 100, text=f"{p}%")
            st.write("")

time.sleep(1)
st.rerun()
