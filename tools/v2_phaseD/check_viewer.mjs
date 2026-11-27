import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { chromium } from 'playwright-core';

const url = process.env.SUZU_VIEWER_URL ?? 'http://127.0.0.1:8765/viewer/';
const out = process.env.SUZU_QA_DIR ?? 'viewer-qa';
const screenshot = async (page, file, options={}) => page.screenshot({path:path.join(out,file),...options});
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
await mkdir(out,{recursive:true});
const browser = await chromium.launch({
 executablePath: process.env.SUZU_CHROMIUM || undefined, headless:true,
 args: ['--no-sandbox','--no-zygote','--single-process','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']
});
const errors=[], network=[], blocked=[], glErrors=[];
const startTest = async (context) => {
 await context.route('**/*', async route=>{
  const u = new URL(route.request().url());
  if(u.protocol==='http:' && u.hostname==='127.0.0.1') return route.continue();
  blocked.push(u.href); await route.abort();
 });
 await context.addInitScript(()=>{
  const go=HTMLCanvasElement.prototype.getContext;
  window.suzuWebGL = [];
  HTMLCanvasElement.prototype.getContext=function (type,...args) {
   const gl=go.call(this,type,...args);
   if(gl && (type==='webgl2'||type==='webgl')&&!window.suzuWebGL.includes(gl))window.suzuWebGL.push(gl);
   return gl;
  };
 });
 const page=await context.newPage();
 page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
 page.on('pageerror',err=>errors.push(err.message));
 page.on('response',res=>{if(res.status()>=400)network.push([res.status(),res.url()]);});
 const u=new URL(url);u.searchParams.set('check','1');
 await page.goto(u.href,{waitUntil:'networkidle',timeout:90000});
 await page.waitForFunction(()=>window.suzuViewer?.getState().ready,undefined,{timeout:90000});
 await page.locator('.ready[data-state=ready]').waitFor();
 return page;
};
const state = async (p)=>p.evaluate(()=>window.suzuViewer.getState());
const checkGL = async (p) => {
 const l=await p.evaluate(()=>{
  const errors=[];
  for(const gl of window.suzuWebGL){ let n;while((n=gl.getError())!==gl.NO_ERROR){errors.push(n);if(errors.length>20)break;} }
  return {contextCount:window.suzuWebGL.length,errors};
 });
 assert.ok(l.contextCount>0,'No real WebGL context');
 glErrors.push(...l.errors);
};
try {
 const page=await startTest(await browser.newContext({viewport:{width:1168,height:850},deviceScaleFactor:1}));
 const base=await state(page);assert.equal(base.view,'full'); assert.equal(base.mode,'shaded');assert.equal(base.duration,11.4);
 await screenshot(page,'01-shaded.png');
 const full = [base.cameraPosition,base.orbitTarget];
 assert.ok(full[0]?.length===3 && full[1]?.length===3,'Live camera/target diagnostics missing');
 const box = await page.locator('#scene').boundingBox();
 const cX=box.x+box.width*.49, cY=box.y+box.height*.47;
 await page.mouse.move(cX,cY);await page.mouse.down();await page.mouse.move(cX+145,cY+12,{steps:8});await page.mouse.up();
 await page.waitForTimeout(450);assert.notDeepEqual((await state(page)).cameraPosition,full[0],'Drag does not rotate the live camera');
 await page.locator('[data-view=back]').click();await page.waitForTimeout(410);assert.equal((await state(page)).view,'back');
 const back=(await state(page)).cameraPosition;assert.notDeepEqual(back,full[0]);
 await page.mouse.move(cX,cY);await page.mouse.wheel(0,-270);await page.waitForTimeout(400);
 const zoomed=await state(page);assert.notDeepEqual(zoomed.cameraPosition,back,'Wheel does not zoom');
 await page.mouse.move(cX,cY);await page.mouse.down({button:'right'});await page.mouse.move(cX+28,cY+38,{steps:8});await page.mouse.up({button:'right'});
 await page.waitForTimeout(400);assert.notDeepEqual((await state(page)).orbitTarget,zoomed.orbitTarget,'Pan does not translate the live orbit target');
 await page.locator('[data-view=half]').click();await page.locator('[data-mode=clay]').click();
 await page.waitForTimeout(400);assert.equal((await state(page)).mode,'clay');assert.equal((await state(page)).view,'half');await screenshot(page,'02-clay.png');
 await page.locator('[data-mode=wire]').click();await page.waitForTimeout(400);assert.equal((await state(page)).mode,'wire');await screenshot(page,'03-wire.png');
 await page.locator('[data-mode=shaded]').click();await page.locator('[data-view=face]').click();
 await page.waitForTimeout(450);
 const lightHashes=new Set();
 for(const light of ['front','left','right','back']){
  await page.locator(`[data-light=${light}]`).click();await page.waitForTimeout(300);
  assert.equal((await state(page)).light,light);
  lightHashes.add(sha(await page.screenshot({clip:{x:Math.floor(cX-52),y:Math.floor(cY-68),width:104,height:130}})));
 }
 assert.equal(lightHashes.size,4,'Lighting choices must change the live render');
 const exp={};
 for (const expression of ['smile','laugh','closed','surprise']) {
  await page.locator(`[data-expression=${expression}]`).click();await page.waitForTimeout(260);
  const value=await state(page);assert.equal(value.expression,expression);assert.ok(Object.keys(value.morphWeights).length);
  assert.ok(Object.values(value.morphWeights).some(x=>x>.25), 'No real morph target was applied');
  exp[expression]=value.morphWeights;
  await screenshot(page,`04-${expression}.png`);
 }
 assert.equal(new Set(Object.values(exp).map(x=>JSON.stringify(x))).size,4);
 await page.locator('[data-expression=neutral]').click();
 await page.locator('[data-view=full]').click();
 await page.locator('[data-light=front]').click();
 await page.locator('#timeline').evaluate(el=>{el.value='10.2';el.dispatchEvent(new InputEvent('input',{bubbles:true}));});
 await page.waitForTimeout(300);
 let t=(await state(page)).time;assert.ok(Math.abs(t-10.2)<.03);
 await screenshot(page,'05-seek-10s.png');
 await page.locator('#timeline').evaluate(el=>{el.value='3.0';el.dispatchEvent(new InputEvent('input',{bubbles:true}));});
 t=(await state(page)).time;
 await page.locator('#play').click();
 await page.waitForFunction(t=>window.suzuViewer.getState().time>t+.25,t,{timeout:12000});
 const on=await state(page);assert.equal(on.playing,true);assert.notEqual(on.time,t);
 await page.locator('#play').click();const paused=await state(page);assert.equal(paused.playing,false);
 await page.waitForTimeout(250);assert.ok(Math.abs((await state(page)).time-paused.time)<.025,'Pause did not stop timeline');
 await checkGL(page);
 const mobile=page;
 await mobile.setViewportSize({width:390,height:844});
 const cdp=await mobile.context().newCDPSession(mobile);
 await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});
 assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth),390,'Mobile horizontal overflow');
 await mobile.locator('[data-view=face]').click();await mobile.locator('[data-expression=closed]').click();
 await mobile.waitForTimeout(450);
 assert.equal((await state(mobile)).expression,'closed'); await screenshot(mobile,'06-mobile.png',{fullPage:true});await checkGL(mobile);
 const result={ready:base.ready,duration:base.duration,viewModes:3,presets:lightHashes.size,expressions:Object.keys(exp),
                 verifiedOrbitZoomPan:true,verifiedPlayPauseScrub:true,verifiedMobile:true,network,blocked,errors,glErrors};
 await writeFile(path.join(out,'browser-report.json'),JSON.stringify(result,null,2)+'\n');
 assert.deepEqual(network,[]);assert.deepEqual(blocked,[]);assert.deepEqual(errors,[]);assert.deepEqual(glErrors,[]);
 console.log(JSON.stringify(result));
} finally {
 await browser.close();
}
