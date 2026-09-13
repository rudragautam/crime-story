const fs = require("fs");
const { chromium } = require("playwright");
const { spawn } = require("child_process");

const manifestPath = process.argv[2];
const outputPath = process.argv[3];

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const WIDTH = 1280;
const HEIGHT = 720;
const FPS = 12;

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{box-sizing:border-box}
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#070707;color:#eee}
body{font-family:Arial,Helvetica,sans-serif}
#scene{position:relative;width:100vw;height:100vh;overflow:hidden;background:#080808}
#bg{position:absolute;inset:-4%;transition:transform .2s linear}
#vignette{position:absolute;inset:0;background:radial-gradient(circle at 52% 46%,transparent 22%,rgba(0,0,0,.12) 52%,rgba(0,0,0,.82) 100%);z-index:5}
#grain{position:absolute;inset:0;z-index:6;opacity:.055;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.frame{position:absolute;inset:24px;border:1px solid rgba(255,255,255,.16);z-index:8}
.frame:before,.frame:after{content:"";position:absolute;width:44px;height:44px;border-color:#c92323;border-style:solid}
.frame:before{left:-1px;top:-1px;border-width:3px 0 0 3px}
.frame:after{right:-1px;bottom:-1px;border-width:0 3px 3px 0}
.top{position:absolute;left:62px;right:62px;top:42px;display:flex;justify-content:space-between;z-index:9;font-size:13px;letter-spacing:3px;color:#aaa}
.brand{color:#e33434;font-weight:800}
.chapter{position:absolute;left:72px;bottom:185px;z-index:9;font-size:14px;letter-spacing:4px;color:#e33434;font-weight:700}
.caption{position:absolute;left:72px;right:180px;bottom:82px;z-index:9;font-family:Georgia,serif;font-size:34px;line-height:1.12;letter-spacing:.2px;text-shadow:0 3px 14px #000;max-width:940px}
.rule{position:absolute;left:72px;bottom:155px;width:82px;height:2px;background:#d52b2b;z-index:9}
.small{position:absolute;right:72px;bottom:52px;z-index:9;font-size:11px;letter-spacing:2px;color:#777}
</style>
</head>
<body>
<div id="scene">
  <div id="bg"></div><div id="vignette"></div><div id="grain"></div>
  <div class="frame"></div>
  <div class="top"><span class="brand">CRIME STORY</span><span id="counter"></span></div>
  <div class="chapter" id="chapter"></div><div class="rule"></div>
  <div class="caption" id="caption"></div>
  <div class="small">DOCUMENTARY FILE</div>
</div>
<script>
const scene = ${JSON.stringify(manifest.scenes[0])};
const palettes = {
 rio_night:["#07090d","#111d29","#6c1717"], case_file:["#0b0b0b","#242020","#791b1b"],
 timeline:["#090a0d","#171b22","#8b2020"], phone:["#06090c","#14202b","#9b1e1e"],
 money:["#090b09","#162018","#6f1e1e"], rio_case:["#08090d","#20202b","#a02121"],
 payment:["#0b0909","#201916","#8b1e1e"], evidence:["#09090a","#1d1d1e","#9a2020"],
 arrest:["#08090b","#171a20","#a32222"], court:["#090909","#201d1d","#8d1f1f"],
 verdict:["#080808","#241c1c","#b52727"], ending:["#070707","#151515","#8e2020"]
};
function svgFor(type, t){
 const p=palettes[type]||palettes.case_file;
 const cx=640+Math.sin(t*.7)*80, cy=330+Math.cos(t*.55)*25;
 let shapes="";
 if(type.includes("rio")) shapes = `<circle cx="970" cy="150" r="70" fill="${p[2]}" opacity=".55"/><path d="M0 560 Q260 430 500 560 T1000 540 T1400 560 V720 H0Z" fill="${p[1]}"/><path d="M780 530 L880 300 L980 530Z" fill="#111"/><rect x="850" y="360" width="58" height="170" fill="#070707"/>`;
 else if(type==="phone") shapes = `<rect x="510" y="105" width="260" height="500" rx="30" fill="#111" stroke="${p[2]}" stroke-width="5"/><rect x="535" y="145" width="210" height="390" rx="8" fill="#0b1116"/><circle cx="640" cy="568" r="18" fill="#222"/><path d="M565 230h150M565 285h115M565 340h145" stroke="#8c8c8c" stroke-width="7" opacity=".5"/>`;
 else if(type==="money"||type==="payment") shapes = `<rect x="310" y="245" width="660" height="230" rx="18" fill="#101510" stroke="${p[2]}" stroke-width="5"/><circle cx="640" cy="360" r="70" fill="none" stroke="#677d65" stroke-width="7"/><text x="640" y="388" text-anchor="middle" font-size="72" fill="#899f87">$</text>`;
 else if(type==="timeline") shapes = `<path d="M180 360 H1100" stroke="${p[2]}" stroke-width="8"/><g fill="#ddd"><circle cx="270" cy="360" r="15"/><circle cx="500" cy="360" r="15"/><circle cx="740" cy="360" r="15"/><circle cx="970" cy="360" r="15"/></g>`;
 else if(type==="court"||type==="verdict") shapes = `<path d="M380 210h520M450 210v300M830 210v300M340 510h600" stroke="#777" stroke-width="12"/><path d="M410 280h420" stroke="${p[2]}" stroke-width="8"/><path d="M520 510v-150M640 510v-150M760 510v-150" stroke="#555" stroke-width="8"/>`;
 else if(type==="evidence") shapes = `<g stroke="${p[2]}" fill="none" stroke-width="5"><rect x="280" y="180" width="300" height="190"/><rect x="610" y="280" width="300" height="190"/><path d="M580 275L610 315M580 335L610 360M700 240L830 460"/></g>`;
 else if(type==="arrest") shapes = `<circle cx="640" cy="280" r="105" fill="#151515" stroke="${p[2]}" stroke-width="5"/><path d="M510 570 Q640 380 770 570" fill="#111" stroke="#444" stroke-width="4"/><path d="M530 410L750 410" stroke="${p[2]}" stroke-width="7"/>`;
 else shapes = `<rect x="330" y="180" width="620" height="350" fill="#101010" stroke="#444" stroke-width="4"/><path d="M390 250h500M390 310h420M390 370h470M390 430h330" stroke="#666" stroke-width="8" opacity=".65"/>`;
 return `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><radialGradient id="g"><stop stop-color="${p[1]}"/><stop offset="1" stop-color="${p[0]}"/></radialGradient></defs><rect width="1280" height="720" fill="url(#g)"/><circle cx="${cx}" cy="${cy}" r="280" fill="${p[2]}" opacity=".09"/>${shapes}</svg>`;
}
window.setScene=(s,index)=>{
 document.getElementById("chapter").textContent=s.chapter;
 document.getElementById("caption").textContent=s.caption||"";
 document.getElementById("counter").textContent=String(index+1).padStart(2,"0")+" / 12";
 document.getElementById("bg").innerHTML=svgFor(s.visual,index);
};
</script>
</body></html>`;

(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:WIDTH,height:HEIGHT},deviceScaleFactor:1});
 await page.setContent(html);
 const ff=spawn("ffmpeg",[
   "-y","-f","image2pipe","-vcodec","png","-r",String(FPS),"-i","-",
   "-an","-c:v","libx264","-preset","veryfast","-crf","30",
   "-pix_fmt","yuv420p","-movflags","+faststart",outputPath
 ],{stdio:["pipe","inherit","inherit"]});

 for(let i=0;i<manifest.scenes.length;i++){
   const s=manifest.scenes[i];
   await page.evaluate(({s,i})=>window.setScene(s,i),{s,i});
   const frames=Math.max(1,Math.ceil(s.duration*FPS));
   for(let f=0;f<frames;f++){
     const p=await page.screenshot({type:"png"});
     if(!ff.stdin.write(p)) await new Promise(r=>ff.stdin.once("drain",r));
   }
 }
 ff.stdin.end();
 await new Promise((resolve,reject)=>{
   ff.on("close",code=>code===0?resolve():reject(new Error("ffmpeg exited "+code)));
 });
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
