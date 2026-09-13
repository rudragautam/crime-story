import json
import os
import re
import subprocess
from pathlib import Path
from html import unescape

import requests
from google import genai


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WORK = ROOT / "work"
DATA = ROOT / "data"
STORIES = ROOT / "stories"
TOOLS = ROOT / "tools"

for p in (OUT, WORK, DATA):
    p.mkdir(parents=True, exist_ok=True)

STORY_ID = os.environ.get("STORY_ID", "sikkema")
STORY_FILE = STORIES / STORY_ID / "story.json"
STATE_FILE = DATA / "crime_state.json"

# Official source used by the current Sikkema test story.
DOJ_URL = (
    "https://www.justice.gov/usao-sdny/pr/"
    "us-attorney-announces-conviction-daniel-sikkema-murder-hire"
)

# The existing renderer expects these visual labels.
# The story JSON stores the real local visual paths.
VISUAL_LABELS = {
    "rio_night_cityscape.jpg": "rio_night",
    "rio_street_night.jpg": "rio_case",
    "smartphone_dark_table.jpg": "phone",
    "overhead_map_investigation.jpg": "timeline",
    "dark_investigative_desk.jpg": "evidence",
    "dark_wooden_desk.jpg": "case_file",
    "investigative_desk_noir.jpg": "money",
    "silhouette_city_night.jpg": "arrest",
    "courthouse_dusk_moody.jpg": "court",
    "empty_courthouse_corridor.jpg": "verdict",
    "noir_office_haze.jpg": "ending",
}


def clean_html(raw):
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def fetch_source(url=DOJ_URL):
    print(f"Fetching source: {url}")
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "crime-story/1.0"},
    )
    response.raise_for_status()
    return clean_html(response.text)


def flatten_story(story):
    """
    Convert the approved story schema:
        chapters[].segments[]
    into the temporary renderer schema:
        scenes[]
    without changing stories/<id>/story.json.
    """
    scenes = []

    for chapter in story.get("chapters", []):
        chapter_title = chapter.get("title", "CASE FILE")

        for segment in chapter.get("segments", []):
            visual_path = segment.get("visual", "")
            filename = Path(visual_path).name
            visual_label = VISUAL_LABELS.get(filename, "case_file")

            scenes.append(
                {
                    "chapter": chapter_title,
                    "title": chapter_title,
                    "narration": re.sub(
                        r"\s+",
                        " ",
                        segment.get("narration", ""),
                    ).strip(),
                    "caption": segment.get("caption", ""),
                    "visual": visual_label,
                    "visual_path": visual_path,
                    "motion": segment.get("motion", "slow_push_in"),
                    "fact_status": segment.get("fact_status", "established"),
                    "segment_id": segment.get("id", ""),
                }
            )

    # Keep an explicit ending as the final scene for the current renderer.
    ending = story.get("ending")
    if ending and ending.get("narration"):
        visual_path = ending.get("visual", "")
        filename = Path(visual_path).name
        scenes.append(
            {
                "chapter": "ENDING",
                "title": story.get("title", "THE END"),
                "narration": re.sub(
                    r"\s+",
                    " ",
                    ending.get("narration", ""),
                ).strip(),
                "caption": "",
                "visual": VISUAL_LABELS.get(filename, "ending"),
                "visual_path": visual_path,
                "motion": ending.get("motion", "very_slow_pull_back"),
                "fact_status": "established",
                "segment_id": "ending",
            }
        )

    return scenes


def load_story():
    if not STORY_FILE.exists():
        raise FileNotFoundError(
            f"Story file not found: {STORY_FILE}"
        )

    story = json.loads(STORY_FILE.read_text(encoding="utf-8"))

    if "chapters" in story:
        scenes = flatten_story(story)
    elif "scenes" in story:
        scenes = story["scenes"]
    else:
        raise ValueError(
            "Story JSON must contain either 'chapters' or 'scenes'."
        )

    if not scenes:
        raise ValueError("Story contains no scenes.")

    story["_render_scenes"] = scenes
    return story


def maybe_generate_story(source_text, base_story):
    """
    Gemini is optional. The approved local story remains the source of truth
    unless explicitly enabled with GENERATE_STORY=true.
    """
    if os.environ.get("GENERATE_STORY", "").lower() != "true":
        print("Using approved story JSON; Gemini generation disabled.")
        return base_story

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY missing; using approved story JSON.")
        return base_story

    print("Generating story with Gemini...")
    client = genai.Client(api_key=key)

    prompt = f"""
You are writing a serious US crime documentary script.

SOURCE:
{source_text[:30000]}

Rewrite the existing approved story while preserving only facts supported
by the source.

Rules:
- Clearly distinguish allegations from the May 22, 2026 conviction.
- Do not invent motives, dialogue, forensic details, emotions, or evidence.
- No graphic descriptions.
- Keep the documentary tone cinematic and factual.
- Return JSON only.
"""

    try:
        result = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
            contents=prompt,
        )
        text = result.text.strip()
        text = re.sub(
            r"^```json\s*|\s*```$",
            "",
            text,
            flags=re.I,
        )
        generated = json.loads(text)

        # Do not accept an incompatible schema.
        if "chapters" not in generated and "scenes" not in generated:
            raise ValueError("Gemini returned an incompatible story schema.")

        return generated

    except Exception as exc:
        print(f"Gemini generation failed: {exc}")
        print("Continuing with approved story JSON.")
        return base_story


def synthesize(scene, idx):
    """Temporary AWS-free test narration."""
    text = re.sub(r"\s+", " ", scene["narration"]).strip()
    if not text:
        raise ValueError(f"Scene {idx + 1} has empty narration.")

    path = WORK / f"scene_{idx:02d}.wav"

    subprocess.run(
        [
            "espeak",
            "-w",
            str(path),
            "-s",
            "150",
            "-v",
            os.environ.get("TEST_TTS_VOICE", "en-us"),
            text,
        ],
        check=True,
    )

    return path


def ffprobe_duration(path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]

    return float(
        subprocess.check_output(command, text=True).strip()
    )


def concat_audio(paths):
    listing = WORK / "audio_concat.txt"

    with listing.open("w", encoding="utf-8") as file:
        for path in paths:
            file.write(f"file '{path.resolve()}'\n")

    output = WORK / "narration.wav"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c:a",
            "pcm_s16le",
            str(output),
        ],
        check=True,
    )

    return output


def main():
    print("=" * 60)
    print("CRIME STORY PIPELINE")
    print("=" * 60)

    story = load_story()

    # Only fetch the source when requested. This keeps the approved local
    # story deterministic for the first production test.
    if os.environ.get("FETCH_SOURCE", "false").lower() == "true":
        source = fetch_source()
        story = maybe_generate_story(source, story)

    scenes = story["_render_scenes"]

    # Write the flattened story used by the renderer.
    render_story = {
        "title": story.get("title", "Crime Story"),
        "subtitle": story.get(
            "subtitle",
            story.get("dek", ""),
        ),
        "scenes": scenes,
    }

    story_output = WORK / "story.json"
    story_output.write_text(
        json.dumps(render_story, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Story: {story.get('title', STORY_ID)}")
    print(f"Scenes: {len(scenes)}")

    audio_paths = []
    durations = []

    for idx, scene in enumerate(scenes):
        print(f"TTS: scene {idx + 1}/{len(scenes)}")
        audio_path = synthesize(scene, idx)
        audio_paths.append(audio_path)
        durations.append(ffprobe_duration(audio_path))

    narration = concat_audio(audio_paths)

    manifest = {
        "title": render_story["title"],
        "dek": render_story["subtitle"],
        "scenes": [
            {
                **scene,
                "duration": round(durations[idx], 3),
                "number": idx + 1,
                "text": scene["narration"],
                "textPosition": (
                    "left"
                    if idx % 3 == 0
                    else "right"
                    if idx % 3 == 1
                    else "center"
                ),
            }
            for idx, scene in enumerate(scenes)
        ],
    }

    manifest_path = WORK / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    renderer = TOOLS / "render_crime.js"

    if not renderer.exists():
        raise FileNotFoundError(
            f"Renderer not found: {renderer}"
        )

    silent_video = WORK / "silent.mp4"

    print("Rendering cinematic video...")
    subprocess.run(
        [
            "node",
            str(renderer),
            str(manifest_path),
            str(silent_video),
        ],
        check=True,
    )

    final = OUT / "crime-story-test.mp4"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(narration),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "29",
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(final),
        ],
        check=True,
    )

    meta = {
        "story_id": STORY_ID,
        "title": render_story["title"],
        "scenes": len(scenes),
        "duration_seconds": round(
            ffprobe_duration(final),
            2,
        ),
        "file_size_mb": round(
            final.stat().st_size / 1024 / 1024,
            2,
        ),
    }

    (OUT / "manifest.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("BUILD COMPLETE")
    print(json.dumps(meta, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
