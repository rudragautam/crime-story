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

function fileUrl(filePath) {
  const absolute = path.resolve(ROOT, filePath);
  if (!fs.existsSync(absolute)) {
    console.warn(`WARNING: visual not found: ${absolute}`);
    return "";
  }
  return "file://" + encodeURI(absolute.replace(/\\/g, "/"));
}

function resolveImage(scene) {
  for (const candidate of [scene.visual_path, scene.image]) {
    if (!candidate) continue;
    const absolute = path.isAbsolute(candidate)
      ? candidate
      : path.join(ROOT, candidate);
    if (fs.existsSync(absolute) && fs.statSync(absolute).isFile()) {
      return fileUrl(absolute);
    }
  }
  return "";
}

function buildStory() {
  const scenes = (manifest.scenes || []).map((s, i) => ({
    chapter: s.chapter || "CASE FILE",
    title: s.title || s.chapter || "CASE FILE",
    text: s.text || s.narration || "",
    image: resolveImage(s),
    textPosition:
      s.textPosition ||
      (i % 3 === 0 ? "left" : i % 3 === 1 ? "right" : "center"),
    status: s.fact_status || "ESTABLISHED",
    number: s.number || i + 1,
    sceneLabel: s.segment_id || `SCENE ${String(i + 1).padStart(2, "0")}`,
    metaLabel: s.chapter || "CASE FILE",
    duration: Number(s.duration) || 5,
    zoom: s.zoom || "1.05"
  }));

  return {
    series: {
      name: "CRIME FILES",
      mark: "CF",
      kicker: "TRUE CRIME DOCUMENTARY",
      tagline: "CASE FILE"
    },
    theme: {
      bg: "#050607",
      white: "#f5f3ef",
      muted: "#a8a4a0",
      red: "#b51f28",
      redLight: "#e3484f",
      redGlow: "rgba(181,31,40,.30)",
      imageOpacity: "0.72"
    },
    intro: {
      image: fileUrl("visuals/intro/true_crime_office_night.jpg"),
      kicker: "CASE FILE",
      title: manifest.title || "THE KILLING IN RIO",
      subtitle: manifest.dek || "The Murder-for-Hire Case of Brent Sikkema",
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
  const story = buildStory();

  const injected = `<script>window.CRIME_STORY = ${JSON.stringify(story)};</script>`;
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

  await page.goto("file://" + renderedHtml.replace(/\\/g, "/"), {
    waitUntil: "load"
  });

  await page.waitForFunction(() => {
    return document.querySelectorAll(".slide").length >= 2;
  });
  await page.waitForTimeout(500);

  const fps = 30;
  const durations = [
    Number(story.intro.duration) || 5,
    ...story.scenes.map(s => Number(s.duration) || 5),
    Number(story.outro.duration) || 5
  ];

  const slides = await page.locator(".slide").count();
  if (slides !== durations.length) {
    throw new Error(
      `Template slide count mismatch: ${slides} vs ${durations.length}`
    );
  }

  const framesDir = path.join(ROOT, "work", "frames");
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });

  let frameNo = 0;

  for (let i = 0; i < slides; i++) {
    await page.evaluate(index => {
      document.querySelectorAll(".slide").forEach((el, n) => {
        el.style.display = n === index ? "block" : "none";
        el.classList.toggle("active", n === index);
      });
      window.scrollTo(0, 0);
    }, i);

    await page.waitForTimeout(100);

    const frameCount = Math.max(1, Math.round(durations[i] * fps));

    for (let f = 0; f < frameCount; f++) {
      const progress = f / Math.max(1, frameCount - 1);

      await page.evaluate(p => {
        const slide = [...document.querySelectorAll(".slide")]
          .find(el => el.style.display !== "none");
        if (slide) slide.style.setProperty("--render-progress", p);
      }, progress);

      await page.screenshot({
        path: path.join(
          framesDir,
          `frame_${String(frameNo).padStart(7, "0")}.png`
        ),
        type: "png"
      });

      frameNo++;
    }

    console.log(`Rendered slide ${i + 1}/${slides}`);
  }

  await browser.close();

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const result = spawnSync("ffmpeg", [
    "-y",
    "-framerate", String(fps),
    "-i", path.join(framesDir, "frame_%07d.png"),
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    outputPath
  ], { stdio: "inherit" });

  if (result.status !== 0) {
    throw new Error("ffmpeg encoding failed.");
  }

  console.log(`VIDEO READY: ${outputPath}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
