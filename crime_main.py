<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{{TITLE}}</title>
<style>
:root{
  --bg:#050607;
  --white:#f2f2f2;
  --muted:#a6a6a6;
  --red:#b51f28;
  --red-light:#e3484f;
  --red-glow:rgba(181,31,40,.35);
  --image-opacity:.72;
}
*{box-sizing:border-box}
html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--white);font-family:Arial,Helvetica,sans-serif}
body{overflow:hidden}
#app{width:100vw;height:100vh;overflow-y:auto;scroll-snap-type:y mandatory;scroll-behavior:smooth}
.slide{
  position:relative;width:100vw;height:100vh;min-height:100vh;
  overflow:hidden;scroll-snap-align:start;background:#050607;
}
.bg{
  position:absolute;inset:0;background-size:cover;background-repeat:no-repeat;
  background-position:center;opacity:var(--image-opacity);
  transform:scale(1.04);transition:transform 1s ease,background-position .5s ease;
}
.slide.active .bg{transform:scale(var(--zoom,1.08))}
.overlay{
  position:absolute;inset:0;
  background:
    linear-gradient(90deg,rgba(5,6,7,.94) 0%,rgba(5,6,7,.72) 38%,rgba(5,6,7,.22) 72%,rgba(5,6,7,.58) 100%),
    linear-gradient(0deg,rgba(5,6,7,.82),transparent 35%,rgba(5,6,7,.25));
}
.grain{position:absolute;inset:0;opacity:.055;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140' viewBox='0 0 140 140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.8'/%3E%3C/svg%3E")}
.frame{position:absolute;inset:24px;border:1px solid rgba(255,255,255,.10);pointer-events:none}
.frame:before,.frame:after{content:"";position:absolute;width:42px;height:42px;border-color:var(--red);border-style:solid}
.frame:before{left:-1px;top:-1px;border-width:2px 0 0 2px}
.frame:after{right:-1px;bottom:-1px;border-width:0 2px 2px 0}
.topbar{position:absolute;top:34px;left:48px;right:48px;display:flex;justify-content:space-between;align-items:center;z-index:5;text-transform:uppercase;letter-spacing:.16em;font-size:11px}
.brand{display:flex;gap:12px;align-items:center;font-weight:700}
.brand-mark{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid var(--red);color:var(--red-light);font-size:10px}
.case-status{color:#ddd}
.case-status:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--red);margin-right:9px;box-shadow:0 0 15px var(--red-glow)}
.story-content{position:absolute;z-index:4;top:50%;transform:translateY(-50%);width:min(720px,62vw)}
.story-content.left{left:8vw}
.story-content.center{left:50%;transform:translate(-50%,-50%);text-align:center}
.story-content.right{right:8vw}
.chapter{font-size:12px;letter-spacing:.32em;color:var(--red-light);text-transform:uppercase;margin-bottom:18px;font-weight:700}
.story-title{font-size:clamp(42px,5.3vw,88px);line-height:.94;letter-spacing:-.035em;text-transform:uppercase;margin:0 0 24px;font-weight:800;text-shadow:0 5px 30px rgba(0,0,0,.45)}
.divider{width:70px;height:2px;background:var(--red);margin:0 0 24px}
.story-content.center .divider{margin-left:auto;margin-right:auto}
.story-text{font-size:clamp(17px,1.45vw,24px);line-height:1.55;color:#ddd;max-width:680px;margin:0}
.meta{position:absolute;bottom:42px;left:48px;right:48px;z-index:5;display:flex;justify-content:space-between;align-items:end;text-transform:uppercase;letter-spacing:.14em;font-size:10px;color:#aaa}
.scene-label{color:#eee}
.evidence-label{color:#888}
.scene-number{position:absolute;right:48px;top:110px;z-index:5;color:rgba(255,255,255,.15);font-size:86px;font-weight:800;line-height:1}
.progress{position:absolute;left:48px;right:48px;bottom:22px;height:2px;background:rgba(255,255,255,.14);z-index:6}
.progress-fill{height:100%;width:0;background:var(--red);transform-origin:left}
.intro .overlay{background:linear-gradient(90deg,rgba(5,6,7,.88),rgba(5,6,7,.38)),linear-gradient(0deg,rgba(5,6,7,.75),transparent)}
.intro-content{position:absolute;z-index:4;left:8vw;top:50%;transform:translateY(-50%);max-width:1000px}
.intro-kicker{font-size:13px;letter-spacing:.38em;color:var(--red-light);font-weight:700;text-transform:uppercase;margin-bottom:22px}
.intro-title{font-size:clamp(58px,8vw,138px);line-height:.86;letter-spacing:-.055em;text-transform:uppercase;margin:0 0 25px;font-weight:900}
.intro-subtitle{font-size:clamp(18px,1.8vw,29px);color:#d1d1d1;letter-spacing:.02em;max-width:800px}
.outro .overlay{background:linear-gradient(90deg,rgba(5,6,7,.9),rgba(5,6,7,.45)),linear-gradient(0deg,rgba(5,6,7,.88),rgba(5,6,7,.2))}
.outro-content{position:absolute;z-index:4;left:8vw;bottom:13vh;max-width:900px}
.outro-kicker{font-size:12px;letter-spacing:.34em;color:var(--red-light);text-transform:uppercase;font-weight:700;margin-bottom:20px}
.outro-title{font-size:clamp(46px,6vw,100px);line-height:.9;text-transform:uppercase;letter-spacing:-.045em;margin:0 0 20px}
.outro-subtitle{font-size:18px;color:#aaa}
.hidden{display:none}
@media(max-width:800px){
  .topbar{left:28px;right:28px}.meta{left:28px;right:28px}.progress{left:28px;right:28px}
  .frame{inset:14px}.story-content.left,.story-content.right,.intro-content,.outro-content{left:7vw;right:7vw;width:auto}
  .story-content.right{right:7vw}.scene-number{right:28px;top:90px}
}
</style>
</head>
<body>
<div id="app"></div>

<script>
/*
  MASTER TEMPLATE
  ----------------
  This file is intentionally content-free.

  Recommended runtime:
    1. Load stories/<case>/story.json
    2. Resolve visual paths
    3. Inject the object into window.CRIME_STORY
    4. This template renders every slide dynamically.

  If opened directly without injected data, the template uses a tiny
  placeholder so the page does not crash. Production rendering should
  always inject real story data.
*/

window.CRIME_STORY = window.CRIME_STORY || {
  series:{name:"CRIME FILES",mark:"CF",kicker:"INVESTIGATIVE DOCUMENTARY",tagline:""},
  theme:{},
  intro:{image:"",kicker:"",title:"",subtitle:""},
  scenes:[],
  outro:{image:"",kicker:"",title:"",subtitle:""}
};

const app=document.getElementById("app");

function esc(value){
  return String(value ?? "")
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;")
    .replace(/'/g,"&#039;");
}

function resolveImage(path){
  if(!path) return "";
  if(/^https?:\/\//i.test(path) || /^data:/i.test(path) || /^file:/i.test(path)) return path;
  return path.replace(/\\/g,"/");
}

function applyTheme(story){
  const t=story.theme||{};
  const root=document.documentElement;
  const map={
    "--bg":t.bg,"--white":t.white,"--muted":t.muted,
    "--red":t.red,"--red-light":t.redLight,
    "--red-glow":t.redGlow
  };
  Object.entries(map).forEach(([k,v])=>{if(v)root.style.setProperty(k,v)});
  if(t.imageOpacity!=null) root.style.setProperty("--image-opacity",t.imageOpacity);
  document.title=story.title || story.series?.name || "Crime Documentary";
}

function topbar(series,status){
  return `
    <div class="topbar">
      <div class="brand">
        <span class="brand-mark">${esc(series.mark||"CF")}</span>
        <span class="series-name">${esc(series.name||"")}</span>
      </div>
      <div class="case-status">
        <span class="case-status-text">${esc(status||series.kicker||"")}</span>
      </div>
    </div>`;
}

function frame(){
  return `<div class="frame"></div><div class="grain"></div>`;
}

function buildIntro(story){
  const i=story.intro||{};
  return `
  <section class="slide intro" data-duration="${Number(i.duration||6)}">
    <div class="bg" style="background-image:url('${esc(resolveImage(i.image))}')"></div>
    <div class="overlay"></div>
    ${frame()}
    ${topbar(story.series||{},"")}
    <div class="intro-content">
      <div class="intro-kicker">${esc(i.kicker)}</div>
      <h1 class="intro-title">${esc(i.title)}</h1>
      <div class="intro-subtitle">${esc(i.subtitle)}</div>
    </div>
    <div class="meta"><div class="scene-label">${esc(story.series?.tagline||"")}</div><div class="evidence-label">CASE FILE</div></div>
    <div class="progress"><div class="progress-fill"></div></div>
  </section>`;
}

function buildScene(scene,index,series){
  const pos=["left","center","right"].includes(scene.textPosition)?scene.textPosition:"left";
  const duration=Number(scene.duration||8);
  const zoom=Number(scene.zoom||1.08);
  const image=resolveImage(scene.image || scene.visual);
  return `
  <section class="slide scene" data-index="${index}" data-duration="${duration}" style="--zoom:${zoom}">
    <div class="bg" style="background-image:url('${esc(image)}');background-position:${esc(scene.imagePosition||"center")}"></div>
    <div class="overlay"></div>
    ${frame()}
    ${topbar(series,scene.status||scene.chapter||"")}
    <div class="scene-number">${esc(scene.number||String(index+1).padStart(2,"0"))}</div>
    <div class="story-content ${pos}">
      <div class="chapter">${esc(scene.chapter)}</div>
      <h2 class="story-title">${esc(scene.title)}</h2>
      <div class="divider"></div>
      <p class="story-text">${esc(scene.text||scene.narration)}</p>
    </div>
    <div class="meta">
      <div class="scene-label">${esc(scene.sceneLabel||"")}</div>
      <div class="evidence-label">${esc(scene.metaLabel||"")}</div>
    </div>
    <div class="progress"><div class="progress-fill"></div></div>
  </section>`;
}

function buildOutro(story){
  const o=story.outro||{};
  return `
  <section class="slide outro" data-duration="${Number(o.duration||7)}">
    <div class="bg" style="background-image:url('${esc(resolveImage(o.image))}')"></div>
    <div class="overlay"></div>
    ${frame()}
    ${topbar(story.series||{},"")}
    <div class="outro-content">
      <div class="outro-kicker">${esc(o.kicker)}</div>
      <h2 class="outro-title">${esc(o.title)}</h2>
      <div class="outro-subtitle">${esc(o.subtitle)}</div>
    </div>
    <div class="meta"><div class="scene-label">${esc(story.series?.name||"")}</div><div class="evidence-label">END</div></div>
    <div class="progress"><div class="progress-fill"></div></div>
  </section>`;
}

function build(story){
  const scenes=Array.isArray(story.scenes)?story.scenes:[];
  app.innerHTML=
    buildIntro(story)+
    scenes.map((s,i)=>buildScene(s,i,story.series||{})).join("")+
    buildOutro(story);
  observeSlides();
}

let timer=null;
let activeSlide=null;

function startProgress(slide){
  clearTimeout(timer);
  document.querySelectorAll(".progress-fill").forEach(x=>{
    x.style.transition="none";
    x.style.width="0%";
  });
  if(!slide) return;
  const fill=slide.querySelector(".progress-fill");
  const duration=Math.max(0.1,Number(slide.dataset.duration||8));
  requestAnimationFrame(()=>{
    fill.style.transition=`width ${duration}s linear`;
    fill.style.width="100%";
  });
  timer=setTimeout(()=>{},duration*1000);
}

function observeSlides(){
  const slides=[...document.querySelectorAll(".slide")];
  const io=new IntersectionObserver(entries=>{
    entries.forEach(entry=>{
      if(entry.isIntersecting && entry.intersectionRatio>=.6){
        slides.forEach(s=>s.classList.remove("active"));
        entry.target.classList.add("active");
        activeSlide=entry.target;
        startProgress(activeSlide);
      }
    });
  },{threshold:[.6]});
  slides.forEach(s=>io.observe(s));
}

function setStory(story){
  if(!story || typeof story!=="object") throw new Error("Invalid CRIME_STORY object");
  window.CRIME_STORY=story;
  applyTheme(story);
  build(story);
}

applyTheme(window.CRIME_STORY);
build(window.CRIME_STORY);
window.setCrimeStory=setStory;
</script>
</body>
</html>