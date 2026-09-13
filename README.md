# Crime Story

Generic long-form crime documentary automation.

## What this version does

- Pulls a primary DOJ source.
- Generates a continuous documentary script with Gemini.
- Uses local eSpeak only for the temporary preview; AWS/Polly is intentionally disabled. Gemini uses the current `gemini-3.6-flash` model.
- Renders a restrained 16:9 cinematic sequence.
- Uses short typewriter-style captions instead of full-screen paragraphs.
- Produces a 720p H.264 test MP4 with a deliberately smaller bitrate/CRF target.
- Does **not** upload to YouTube yet.

## GitHub Actions secrets

Add these repository secrets:

- `GEMINI_API_KEY`
- `GEMINI_API_KEY` only

Never commit AWS credentials or API keys.

## Local requirements

- Python 3.12+
- Node 20+
- FFmpeg
- Playwright Chromium

## Test

Run:

```bash
pip install -r requirements.txt
npm install --no-save playwright@1.55.0
npx playwright install --with-deps chromium
python crime_main.py
```

The result is written to:

```text
output/crime-story-test.mp4
```

## Later phases

Amazon Polly and YouTube upload are intentionally disabled during preview testing.

## YouTube upload

Intentionally not included in V2. After the visual/audio test is approved, add a separate private-upload step so the first production run can be reviewed safely.
