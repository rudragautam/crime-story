import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WORK = ROOT / "work"
STORIES = ROOT / "stories"
TOOLS = ROOT / "tools"

for p in (OUT, WORK):
    p.mkdir(parents=True, exist_ok=True)

STORY_ID = os.environ.get("STORY_ID", "sikkema")
STORY_FILE = STORIES / STORY_ID / "story.json"


def flatten_story(story):
    scenes = []
    for chapter in story.get("chapters", []):
        chapter_title = chapter.get("title", "CASE FILE")
        for segment in chapter.get("segments", []):
            scenes.append({
                "id": segment.get("id", ""),
                "chapter": chapter_title,
                "title": segment.get("title", chapter_title),
                "text": re.sub(r"\s+", " ", segment.get("narration", "")).strip(),
                "narration": segment.get("narration", ""),
                "visual_path": segment.get("visual", ""),
                "motion": segment.get("motion", "slow_push_in"),
                "fact_status": segment.get("fact_status", "established"),
            })
    return scenes


def load_story():
    if not STORY_FILE.exists():
        raise FileNotFoundError(f"Story file not found: {STORY_FILE}")
    # Accept both UTF-8 and UTF-8 with BOM.
    story = json.loads(STORY_FILE.read_text(encoding="utf-8-sig"))
    if "chapters" not in story:
        raise ValueError("story.json must contain chapters[].")
    scenes = flatten_story(story)
    if not scenes:
        raise ValueError("story.json contains no segments.")
    return story, scenes


def build_manifest(story, scenes):
    return {
        "story_id": STORY_ID,
        "title": story.get("title", STORY_ID),
        "subtitle": story.get("subtitle", ""),
        "format": story.get("format", "long_form"),
        "aspect_ratio": story.get("aspect_ratio", "16:9"),
        "scenes": [
            {
                **scene,
                "number": i + 1,
            }
            for i, scene in enumerate(scenes)
        ],
        "ending": story.get("ending", {}),
        "tts": {
            "provider": "aws_polly",
            "enabled": True,
            "called_in_this_test": False,
        },
    }


def main():
    print("=" * 60)
    print("CRIME STORY PIPELINE")
    print("=" * 60)

    story, scenes = load_story()
    manifest = build_manifest(story, scenes)

    manifest_path = WORK / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    renderer = TOOLS / "render_crime.js"
    if not renderer.exists():
        raise FileNotFoundError(f"Renderer not found: {renderer}")

    silent_video = WORK / "silent.mp4"

    print(f"Story: {manifest['title']}")
    print(f"Scenes: {len(scenes)}")
    print("Source: stories/<story_id>/story.json")
    print("Visuals: local JPG files from story.json")
    print("TTS: AWS Polly configured, NOT called during visual test")
    print("Rendering HTML template...")

    subprocess.run(
        ["node", str(renderer), str(manifest_path), str(silent_video)],
        check=True,
    )

    final = OUT / "crime-story-test.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(silent_video),
            "-c:v", "copy", "-an", "-movflags", "+faststart", str(final)
        ],
        check=True,
    )

    print("=" * 60)
    print("VISUAL BUILD COMPLETE")
    print(f"Output: {final}")
    print("AWS Polly was NOT called.")
    print("=" * 60)


if __name__ == "__main__":
    main()
