/* Prism Layer Studio v2.2 — reactive SVG prism mesh, self contained and offline.
   Artistic preview: geometry is normalized for visibility, NOT a simulation or mesh-quality guarantee. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const root = $('heroInteractive'), scene = $('heroScene'), base = $('heroMeshBase');
  const reveal = $('heroMeshReveal'), revealCircle = $('heroReveal'), probe = $('heroProbe');
  const tilt = $('sceneTilt'), coords = $('sceneCoordinates');
  const ns = 'http://www.w3.org/2000/svg';
  if (!root || !scene || !base || !reveal || !revealCircle || !probe) return;

  const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let paused = !!reduced, visible = true;
  let targetX = .5, targetY = .5, currentX = .5, currentY = .5;
  let activeIndex = -1, hovering = false, frame = 0;
  let result = {N:10,r:1.2,w:0.00007,T:0.0018,layers:[]};
  let edges = [], paths = [], displayCount = 0;

  const clamp = (x,a,b) => Math.min(b,Math.max(a,x));
  const fmt = (x) => Number.isFinite(x) ? x.toPrecision(4) : '—';
  function make(tag,attrs={},parent) {
    const e = document.createElementNS(ns,tag);
    for (const [name,value] of Object.entries(attrs)) e.setAttribute(name,String(value));
    if (parent) parent.appendChild(e);
    return e;
  }
  function wallY(x){ const t=(x-58)/506; return 291-49*Math.sin(Math.PI*clamp(t,0,1))+4*Math.sin(3.5*Math.PI*t); }
  const mod = x => 1+.055*Math.sin((x-58)/506*Math.PI*2.2);
  function pathLine(offset){
    let s='';for(let j=0;j<=64;j++){const x=58+j*506/64;const y=wallY(x)-offset*mod(x);s+=(j?' L':'M')+x.toFixed(2)+' '+y.toFixed(2);}return s;
  }
  function pathBand(low,high){
    let s=pathLine(high);
    for(let j=64;j>=0;j--){const x=58+j*506/64;const y=wallY(x)-low*mod(x);s+=' L'+x.toFixed(2)+' '+y.toFixed(2);}
    return s+' Z';
  }
  function clear(group){group.replaceChildren();}
  function edgesAtResult() {
    const total=Math.max(1, Math.round(result.N));
    displayCount = Math.min(16,total);
    let cum=[0];
    // Group real layers into at most 16 visual bands; preserve cumulative thickness.
    if (result.layers && result.layers.length===total && Number.isFinite(result.T) && result.T>0) {
      for(let j=1;j<=displayCount;j++){
        const i=Math.max(1,Math.ceil(j*total/displayCount));
        const t=result.layers[i-1].cumulative / result.T;
        cum.push(clamp(t,0,1));
      }
    } else {
      let sum=0;const weights=[];
      for(let j=0;j<displayCount;j++){const t=j/Math.max(1,displayCount-1);const h=Math.pow(clamp(result.r,1,2),t*9);weights.push(h);sum+=h;}
      for(const h of weights) cum.push(cum[cum.length-1]+h/sum);
    }
    edges=cum.map(v=>144*v);
  }
  function build() {
    clear(base);clear(reveal);clear(probe);paths=[];
    edgesAtResult();
    const total=displayCount;
    // Engineering datum line and faint extrusion cues.
    make('path',{d:pathLine(0),class:'hero-wall'},base);
    make('path',{d:pathLine(0),class:'hero-wall'},reveal);
    for(let i=0;i<total;i++){
      const d=pathBand(edges[i],edges[i+1]);paths.push(d);
      make('path',{d,class:'hero-base-layer','data-band':i},base);
      make('path',{d,class:'hero-reveal-layer','data-band':i},reveal);
    }
    for(let i=0;i<=total;i++){
      make('path',{d:pathLine(edges[i]),class:'hero-base-line'},base);
      make('path',{d:pathLine(edges[i]),class:'hero-reveal-line'},reveal);
    }
    for(let j=0;j<=12;j++){
      const x=58+506*j/12;
      const d=`M${x.toFixed(1)},${wallY(x).toFixed(1)} L${x.toFixed(1)},${(wallY(x)-edges[total]*mod(x)).toFixed(1)}`;
      make('path',{d,class:'hero-base-line'},base);
      make('path',{d,class:'hero-reveal-line'},reveal);
    }
    // Gradient edge of physical surface remains visible even outside cursor reveal.
    make('path',{d:pathLine(0),class:'hero-wall'},base);
    selectIndex(activeIndex>=0?Math.min(activeIndex,total-1):-1,false);
  }
  function layerAt(x,y) {
    const xx=58+clamp(x,0,1)*506;
    const sy=wallY(xx)-clamp(y,0,1)*400;
    let best=0,dist=Infinity;
    for(let i=0;i<displayCount;i++){
      const mid=(edges[i]+edges[i+1])/2*mod(xx);
      const d=Math.abs(sy-mid);
      if(d<dist){best=i;dist=d;}
    }
    return best;
  }
  function actualIndex(index) {
    return Math.max(1,Math.ceil((index+1)*result.N/displayCount));
  }
  function selectIndex(index,announce=true) {
    activeIndex=index;
    for(const g of [base,reveal]) for(const p of g.querySelectorAll('[data-band]')){
      p.classList.toggle('hero-selected-layer',Number(p.getAttribute('data-band'))===index);
    }
    if(index<0) return;
    const j=actualIndex(index),item=result.layers && result.layers[j-1];
    const w=item && Number.isFinite(item.thickness)?item.thickness:result.w*Math.pow(result.r,j-1);
    $('heroInspectionLabel').textContent='PRISM LAYER / LOCAL PROBE';
    $('heroInspectionValue').textContent=`第 ${j} 层 · 单层厚度 ${fmt(w*1e6)} μm（预测）`;
    $('heroInspectionIndex').textContent=String(j).padStart(2,'0')+' / '+result.N;
    $('heroFormula').textContent=`h${j} = w · r^${j-1}`;
    if(announce) root.setAttribute('aria-description',`当前选中第 ${j} 层，厚度约 ${fmt(w*1e6)} 微米。`);
  }
  function showProbe(x,y,index){
    clear(probe);
    const xx=58+clamp(x,0,1)*506;
    const c=(edges[index]+edges[index+1])/2;
    const yy=wallY(xx)-c*mod(xx);
    make('line',{x1:xx-15,y1:yy,x2:xx+15,y2:yy},probe);
    make('line',{x1:xx,y1:yy-15,x2:xx,y2:yy+15},probe);
    make('circle',{cx:xx,cy:yy,r:4},probe);
    make('text',{x:xx+16,y:yy-13,class:'probe-text'},probe).textContent='LAYER '+String(actualIndex(index)).padStart(2,'0');
  }
  function getPointer(e){const r=scene.getBoundingClientRect();return {x:clamp((e.clientX-r.left)/r.width,0,1),y:clamp((e.clientY-r.top)/r.height,0,1),px:e.clientX-r.left,py:e.clientY-r.top};}
  function pointMove(e){const p=getPointer(e);hovering=true;targetX=p.x;targetY=p.y;coords.textContent=`X ${p.x.toFixed(3)}  /  Y ${p.y.toFixed(3)}`;if(paused) updateVisual(true);else if(!frame)updateVisual(false);}
  function addRipple(px,py){
    if(paused)return;
    const el=document.createElement('span');el.className='scene-ripple';el.style.left=px+'px';el.style.top=py+'px';$('sceneRipples').appendChild(el);el.addEventListener('animationend',()=>el.remove(),{once:true});
  }
  function pointClick(e){
    const p=getPointer(e);targetX=p.x;targetY=p.y;
    const chosen=layerAt(p.x,p.y);
    selectIndex(chosen);showProbe(p.x,p.y,chosen);addRipple(p.px,p.py);
    if(paused)updateVisual(true);
  }
  function updateVisual(immediate=false){
    if(!visible)return;
    const alpha=immediate||paused?1:.095;
    currentX+=(targetX-currentX)*alpha;currentY+=(targetY-currentY)*alpha;
    const a=(currentX-.5), b=(currentY-.5);
    // Camera-like lag, but limited tilt to avoid discomfort.
    tilt.style.transform=paused?'none':`perspective(1000px) rotateY(${(a*9).toFixed(2)}deg) rotateX(${(-b*7).toFixed(2)}deg) scale(1.025)`;
    revealCircle.setAttribute('cx',(currentX*620).toFixed(1));
    revealCircle.setAttribute('cy',(currentY*400).toFixed(1));
    scene.style.setProperty('--glow-x',(currentX*100).toFixed(2)+'%');
    scene.style.setProperty('--glow-y',(currentY*100).toFixed(2)+'%');
    if(!paused && (Math.abs(currentX-targetX)+Math.abs(currentY-targetY) > .001)) frame=requestAnimationFrame(()=>updateVisual(false));
    else frame=0;
  }
  function setMotion(pausedNow){
    paused=pausedNow;
    document.documentElement.classList.toggle('motion-ready',!paused);
    $('heroMotionToggle').setAttribute('aria-pressed',paused?'true':'false');
    $('heroMotionToggle').textContent=paused?'启用动效':'暂停动效';
    if(paused){cancelAnimationFrame(frame);frame=0;updateVisual(true);}
    else if(visible){cancelAnimationFrame(frame);frame=0;updateVisual(false);}
  }
  scene.addEventListener('pointermove',pointMove,{passive:true});
  scene.addEventListener('pointerenter',()=>{hovering=true;});
  scene.addEventListener('pointerleave',()=>{hovering=false;targetX=.5;targetY=.5;coords.textContent='X 0.500  /  Y 0.500';if(paused)updateVisual(true);else if(!frame)updateVisual(false);});
  scene.addEventListener('click',pointClick);
  root.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','Enter',' '].includes(e.key))return;
    if(e.target!==root)return;
    e.preventDefault();const next=e.key==='ArrowLeft'?((activeIndex-1+displayCount)%displayCount):((activeIndex+1)%displayCount);
    selectIndex(next);showProbe(.5,.5,next);
  });
  $('heroMotionToggle').addEventListener('click',()=>setMotion(!paused));
  $('heroExplore').addEventListener('click',()=>$('inputsSection').scrollIntoView({behavior:paused?'auto':'smooth',block:'start'}));
  if('IntersectionObserver'in window){
    new IntersectionObserver(es=>{
      visible=es.some(e=>e.isIntersecting);
      if(!visible){cancelAnimationFrame(frame);frame=0;}
      else {updateVisual(true);if(!paused)updateVisual(false);}
    },{threshold:.01}).observe(root);
  }
  // Entrance motion is observational and does not change calculation or layout dimensions.
  if('IntersectionObserver' in window && !reduced){
    const elements=[...document.querySelectorAll('main .notice, main .panel')];
    elements.forEach(el=>el.classList.add('reveal-on-scroll'));
    const io=new IntersectionObserver(entries=>{
      for(const e of entries) if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target);}
    },{threshold:.07,rootMargin:'0px 0px -24px 0px'});
    elements.forEach(el=>io.observe(el));
  }
  document.addEventListener('prism:result',e=>{
    result=e.detail;root.classList.remove('hero-invalid');build();
  });
  document.addEventListener('prism:error',()=>{
    root.classList.add('hero-invalid');
    $('heroInspectionLabel').textContent='INVALID DESIGN INPUT';
    $('heroInspectionValue').textContent='请修正参数后重新计算';
    $('heroInspectionIndex').textContent='— / —';
  });
  // app.js dispatches the initial result before this script loads. Read its latest computed model.
  if(window.PrismLayerLatest) result=window.PrismLayerLatest;
  const n=Number($('N').value),r=Number($('r').value);
  if(!window.PrismLayerLatest && Number.isFinite(n)&&n>0)result.N=n;
  if(!window.PrismLayerLatest && Number.isFinite(r)&&r>=1)result.r=r;
  build();setMotion(paused);
})();
