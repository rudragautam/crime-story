import json
import os
import re
import subprocess
import sys
from pathlib import Path
from html import unescape
from urllib.parse import urlparse

import requests
from google import genai

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WORK = ROOT / "work"
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
TOOLS = ROOT / "tools"

for p in (OUT, WORK, DATA):
    p.mkdir(parents=True, exist_ok=True)

DOJ_URL = "https://www.justice.gov/usao-sdny/pr/us-attorney-announces-conviction-daniel-sikkema-murder-hire"
STATE_FILE = DATA / "crime_state.json"

FALLBACK = {
    "title": "The Rio Murder-for-Hire Case",
    "dek": "A contentious divorce. A burner phone. A murder thousands of miles away.",
    "scenes": [
        {
            "chapter": "HOOK",
            "narration": "The murder happened in Rio de Janeiro. But the case investigators built would lead back to a bitter divorce in New York, a burner phone, a trail of payments, and a plan prosecutors said was designed to hide the person behind it.",
            "caption": "THE KILLING HAPPENED IN RIO.",
            "visual": "rio_night",
        },
        {
            "chapter": "CASE INTRO",
            "narration": "The victim was Brent Sikkema. His estranged husband, Daniel Sikkema, was later charged in federal court in New York with arranging a murder-for-hire plot. On May twenty-second, twenty twenty-six, a federal jury found Daniel Sikkema guilty.",
            "caption": "A DIVORCE BECAME THE CENTER OF A FEDERAL CASE.",
            "visual": "case_file",
        },
        {
            "chapter": "TIMELINE",
            "narration": "The alleged planning did not begin on the day of the killing. Prosecutors described communications and payments stretching across the months before Brent Sikkema was killed, creating a timeline investigators could reconstruct after the fact.",
            "caption": "THE TIMELINE STARTED MONTHS BEFORE THE MURDER.",
            "visual": "timeline",
        },
        {
            "chapter": "THE SIGNAL",
            "narration": "According to the indictment, an account on a Brazilian phone was used for communications beginning in August twenty twenty-three. Investigators would later examine the digital trail alongside the financial movements.",
            "caption": "DIGITAL TRACES OUTLIVED THE PEOPLE WHO MADE THEM.",
            "visual": "phone",
        },
        {
            "chapter": "THE MONEY",
            "narration": "The indictment described a series of transfers. One payment was about six hundred dollars. Later transfers totaled roughly twenty-seven hundred dollars and allegedly involved a stolen identity. The amounts mattered because they formed part of a larger pattern.",
            "caption": "THE MONEY LEFT A TRAIL.",
            "visual": "money",
        },
        {
            "chapter": "THE MURDER",
            "narration": "On January fourteenth, twenty twenty-four, Brent Sikkema was murdered in Rio de Janeiro. The killing transformed what had been a hidden plan, according to prosecutors, into a homicide investigation spanning two countries.",
            "caption": "JANUARY 14, 2024 — RIO DE JANEIRO.",
            "visual": "rio_case",
        },
        {
            "chapter": "AFTER THE KILLING",
            "narration": "The next day, according to the indictment, a payment of approximately five thousand dollars was requested through an intermediary. That detail became one of the pieces investigators used to connect the aftermath of the murder to the earlier alleged arrangement.",
            "caption": "THE TRAIL DID NOT END WITH THE KILLING.",
            "visual": "payment",
        },
        {
            "chapter": "THE INVESTIGATION",
            "narration": "Investigators followed communications, money transfers, identities, and the people who connected them. The case was not solved by a single clue. It was assembled from separate pieces that pointed in the same direction.",
            "caption": "ONE CLUE WAS NOT ENOUGH. THE PATTERN WAS.",
            "visual": "evidence",
        },
        {
            "chapter": "THE ARREST",
            "narration": "A person identified in the indictment as a cooperating participant, or CC-1, was arrested on January eighteenth, four days after the murder. The investigation continued, eventually bringing the alleged organizer into a federal prosecution in Manhattan.",
            "caption": "FOUR DAYS AFTER THE MURDER, THE CASE MOVED.",
            "visual": "arrest",
        },
        {
            "chapter": "THE CASE AGAINST SIKKEMA",
            "narration": "Federal prosecutors alleged that Daniel Sikkema had agreed to pay another person to kill his estranged husband and had used intermediaries, payments, and a burner phone in the process. Those allegations were tested in federal court.",
            "caption": "THE ALLEGATIONS WERE TESTED IN FEDERAL COURT.",
            "visual": "court",
        },
        {
            "chapter": "VERDICT",
            "narration": "On May twenty-second, twenty twenty-six, the jury returned a guilty verdict against Daniel Sikkema. The verdict was the endpoint of a case that began with a killing in Brazil and ended in a federal courtroom in New York.",
            "caption": "GUILTY — MAY 22, 2026.",
            "visual": "verdict",
        },
        {
            "chapter": "ENDING",
            "narration": "The case is a reminder of how a crime can leave evidence far beyond the scene itself. Messages, payments, identities, travel, and relationships can become separate threads. Investigators only have to find the pattern that connects them.",
            "caption": "THE SCENE WAS IN RIO. THE EVIDENCE TRAVELED MUCH FARTHER.",
            "visual": "ending",
        },
    ],
}

def clean_html(raw):
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()

def fetch_source():
    r = requests.get(DOJ_URL, timeout=30, headers={"User-Agent": "crime-story/1.0"})
    r.raise_for_status()
    return clean_html(r.text)

def generate_story(source_text):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY missing; using verified fallback story.")
        return FALLBACK

    client = genai.Client(api_key=key)
    prompt = f"""
You are writing a serious US crime documentary script.

SOURCE:
{source_text[:30000]}

Create a continuous 8-10 minute narration about this case.
Important:
- Use ONLY facts supported by the source.
- Clearly distinguish allegations/indictment facts from the May 22, 2026 conviction.
- Do not invent motives, dialogue, forensic details, emotions, or evidence.
- No graphic descriptions.
- Do not write like a news bulletin.
- Make it feel like one continuous documentary story.
- 12 scenes exactly.
- Each scene needs 90-140 words of narration, except the hook and ending may be shorter.
- Captions are short, 5-10 words maximum.
- Visual labels must be one of:
  rio_night, case_file, timeline, phone, money, rio_case, payment,
  evidence, arrest, court, verdict, ending.

Return ONLY JSON:
{{
  "title": "...",
  "dek": "...",
  "scenes": [
    {{"chapter":"...", "narration":"...", "caption":"...", "visual":"..."}}
  ]
}}
"""
    try:
        res = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
            contents=prompt,
        )
        text = res.text.strip()
        text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.I)
        story = json.loads(text)
        if len(story.get("scenes", [])) != 12:
            raise ValueError("Gemini did not return 12 scenes")
        return story
    except Exception as e:
        print(f"Gemini generation failed: {e}; using fallback.")
        return FALLBACK

def synthesize(scene, idx):
    """Temporary AWS-free test narration. Replace with Polly after visual approval."""
    text = re.sub(r"\s+", " ", scene["narration"]).strip()
    path = WORK / f"scene_{idx:02d}.wav"
    subprocess.run([
        "espeak", "-w", str(path), "-s", "150", "-v",
        os.environ.get("TEST_TTS_VOICE", "en-us"),
        text
    ], check=True)
    return path

def ffprobe_duration(path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ]
    return float(subprocess.check_output(cmd, text=True).strip())

def concat_audio(paths):
    listing = WORK / "audio_concat.txt"
    with listing.open("w") as f:
        for p in paths:
            f.write(f"file '{p.resolve()}'\n")
    out = WORK / "narration.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(listing), "-c:a", "pcm_s16le", str(out)
    ], check=True)
    return out

def main():
    print("Fetching DOJ source...")
    source = fetch_source()
    story = generate_story(source)
    (WORK / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")

    audio = []
    durations = []
    for i, scene in enumerate(story["scenes"]):
        print(f"Polly: scene {i+1}/12")
        p = synthesize(scene, i)
        audio.append(p)
        durations.append(ffprobe_duration(p))

    narration = concat_audio(audio)
    manifest = {
        "title": story["title"],
        "dek": story.get("dek", ""),
        "scenes": [
            {**scene, "duration": round(durations[i], 3)}
            for i, scene in enumerate(story["scenes"])
        ],
    }
    (WORK / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Rendering cinematic video...")
    subprocess.run(
        ["node", str(TOOLS / "render_crime.js"), str(WORK / "manifest.json"), str(WORK / "silent.mp4")],
        check=True,
    )

    final = OUT / "crime-story-test.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(WORK / "silent.mp4"),
        "-i", str(narration),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "29",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-shortest", str(final)
    ], check=True)

    meta = {
        "source": DOJ_URL,
        "title": story["title"],
        "duration_seconds": round(ffprobe_duration(final), 2),
        "file_size_mb": round(final.stat().st_size / 1024 / 1024, 2),
    }
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
