const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const TEMPLATE = path.join(ROOT, "templates", "crime_files_16x9.html");
const manifestPath = process.argv[2] || path.join(ROOT, "work", "manifest.json");
const outputPath = process.argv[3] || path.join(ROOT, "work", "silent.mp4");

if (!fs.existsSync(TEMPLATE)) throw new Error(`Template not found: ${TEMPLATE}`);
if (!fs.existsSync(manifestPath)) throw new Error(`Manifest not found: ${manifestPath}`);

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));

function fileUrl(relativePath) {
  if (!relativePath) return "";
  const absolute = path.isAbsolute(relativePath)
    ? relativePath
    : path.join(ROOT, relativePath);
  if (!fs.existsSync(absolute)) {
    throw new Error(`Visual image not found: ${absolute}`);
  }
  return "file://" + encodeURI(absolute.replace(/\\/g, "/"));
}

function makeStory() {
  const scenes = (manifest.scenes || []).map((s, i) => ({
    chapter: s.chapter || "CASE FILE",
    title: s.title || s.chapter || "CASE FILE",
    text: s.text || s.narration || "",
    image: fileUrl(s.visual_path),
    textPosition: ["left", "right", "center"][i % 3],
    status: s.fact_status || "ESTABLISHED",
    number: s.number || i + 1,
    sceneLabel: s.id || `SCENE ${String(i + 1).padStart(2, "0")}`,
    metaLabel: s.chapter || "CASE FILE",
    duration: Number(s.duration) || 6,
    zoom: s.zoom || "1.05"
  }));

  return {
    series: { name: "CRIME FILES", mark: "CF", kicker: "TRUE CRIME DOCUMENTARY", tagline: "CASE FILE" },
    theme: {
      bg: "#050607", white: "#f5f3ef", muted: "#a8a4a0",
      red: "#b51f28", redLight: "#e3484f", redGlow: "rgba(181,31,40,.30)", imageOpacity: "0.72"
    },
    intro: {
      image: fileUrl("visuals/intro/true_crime_office_night.jpg"),
      kicker: "CASE FILE",
      title: manifest.title || "CRIME STORY",
      subtitle: manifest.subtitle || "",
      duration: 5
    },
    scenes,
    outro: {
      image: fileUrl("visuals/outro/noir_office_haze.jpg"),
      kicker: "CASE CLOSED",
      title: "THE END",
      subtitle: "CRIME FILES",
      duration: 5
    }
  };
}

async function main() {
  const template = fs.readFileSync(TEMPLATE, "utf8");
  const story = makeStory();
  const injected = `<script>window.CRIME_STORY=${JSON.stringify(story)};</script>`;
  const html = template.replace("</head>", injected + "</head>");
  const renderedHtml = path.join(ROOT, "work", "rendered_crime.html");
  fs.mkdirSync(path.dirname(renderedHtml), { recursive: true });
  fs.writeFileSync(renderedHtml, html, "utf8");

  const browser = await chromium.launch({
    headless: true,
    args: ["--allow-file-access-from-files"]
  });
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1
  });

  await page.goto("file://" + renderedHtml.replace(/\\/g, "/"), { waitUntil: "load" });
  await page.waitForFunction(() =>
    typeof window.CRIME_STORY !== "undefined" && document.querySelectorAll(".slide").length >= 2
  );

  // Let fonts, backgrounds and CSS settle before capture.
  await page.evaluate(async () => {
    const imgs = [...document.images];
    await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(r => {
      img.addEventListener("load", r, { once: true });
      img.addEventListener("error", r, { once: true });
    })));
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  });

  const slideCount = await page.locator(".slide").count();
  const expected = story.scenes.length + 2;
  if (slideCount !== expected) {
    throw new Error(`Template slide count mismatch: found ${slideCount}, expected ${expected}`);
  }

  const durations = [
    story.intro.duration,
    ...story.scenes.map(s => s.duration),
    story.outro.duration
  ].map(v => Number(v) || 6);

  const fps = 30;
  const framesDir = path.join(ROOT, "work", "frames");
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });

  let frameNo = 0;

  for (let i = 0; i < slideCount; i++) {
    await page.evaluate(index => {
      const slides = [...document.querySelectorAll(".slide")];
      slides.forEach((el, n) => {
        el.style.display = n === index ? "block" : "none";
        el.classList.toggle("active", n === index);
      });
      window.scrollTo(0, 0);
    }, i);

    await page.waitForTimeout(150);

    const frameCount = Math.max(1, Math.round(durations[i] * fps));
    const start = Date.now();

    for (let f = 0; f < frameCount; f++) {
      // Real wall-clock capture: the HTML/CSS typewriter animation plays naturally.
      const target = start + (f * 1000) / fps;
      const wait = target - Date.now();
      if (wait > 0) await new Promise(r => setTimeout(r, wait));

      const frame = path.join(framesDir, `frame_${String(frameNo).padStart(7, "0")}.png`);
      await page.screenshot({ path: frame, type: "png" });
      frameNo++;
    }

    console.log(`Rendered slide ${i + 1}/${slideCount} (${durations[i].toFixed(2)}s)`);
  }

  await browser.close();

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const result = spawnSync("ffmpeg", [
    "-y", "-framerate", String(fps),
    "-i", path.join(framesDir, "frame_%07d.png"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", outputPath
  ], { stdio: "inherit" });

  if (result.status !== 0) throw new Error("FFmpeg encoding failed.");
  console.log(`VIDEO READY: ${outputPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
