/* Browser UI for Prism Layer Studio */
(() => {
  'use strict';
  const core = window.PrismCore;
  const $ = id => document.getElementById(id);
  let mode = 'forward', latest = null, toastTimer;
  const ids = ['rho','viscosity','viscosityMode','geometry','length','U','xFraction','surface','flow','manualCf',
    'targetYplus','N','r','targetTmm','measuredYplus','previousWum','coreCellMm'];
  function number(id) { const v = $(id).value; return v === '' ? NaN : Number(v); }
  function values() { return {
    rho:number('rho'),viscosity:number('viscosity'),viscosityMode:$('viscosityMode').value,
    geometry:$('geometry').value,length:number('length'),U:number('U'),
    xFraction:number('xFraction'),surface:$('surface').value,flow:$('flow').value,
    manualCf:number('manualCf'),targetYplus:number('targetYplus'),N:number('N'),r:number('r'),
    targetTmm:number('targetTmm'),measuredYplus:number('measuredYplus'),
    previousWum:number('previousWum'),coreCellMm:number('coreCellMm'),designMode:mode
  };}
  function scientific(n, digits=9) { return Number(n).toExponential(digits); }
  function format(n, digits=6) {
    if (n === null || !Number.isFinite(n)) return '—';
    if (n === 0) return '0';
    const x = Math.abs(n);
    return x >= 1e5 || x < 1e-3 ? n.toExponential(Math.min(5,digits-1)) : Number(n.toPrecision(digits)).toLocaleString('zh-CN',{maximumFractionDigits:9});
  }
  function lengthHuman(m) {
    if (!Number.isFinite(m)) return '—';
    if (Math.abs(m)>=1) return format(m)+' m';
    if (Math.abs(m)>=1e-3) return format(m*1e3)+' mm';
    if (Math.abs(m)>=1e-6) return format(m*1e6)+' μm';
    return format(m*1e9)+' nm';
  }
  function text(id,s) { $(id).textContent = String(s); }
  function notify(s) { text('toast',s);$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),2600); }
  function modeUpdate() {
    document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));
    $('nRow').hidden = mode==='inverseN';
    $('rRow').hidden = mode==='inverseR';
    $('targetTRow').hidden = !(mode==='inverseN'||mode==='inverseR');
    $('calibrationFields').hidden = mode!=='calibrate';
    text('modeDescription',({forward:'目标 y+、层数 N、增长率 r → 预测首层厚度与总厚度。',
      inverseN:'已知目标 y+、目标总厚度和增长率 → 自动求满足总厚度的最少整数层数。',
      inverseR:'已知目标 y+、目标总厚度和层数 → 数值反求增长率 r。',
      calibrate:'已知旧首层厚度与 STAR-CCM+ 实测 Wall Y+，按比例给出一次修正建议。'})[mode]);
  }
  function geometryUpdate() {
    const geom = $('geometry').value;
    $('outerFields').hidden = geom==='pipe';
    $('sideRow').hidden = geom!=='wing';
    $('lengthLabel').innerHTML = geom==='pipe'?'圆管内径 D <small>m</small>':
      geom==='wing'?'翼型弦长 c <small>m</small>':'平板总长 L <small>m</small>';
  }
  function presetChange() {
    if ($('preset').value==='custom')return;
    const p=core.PRESETS[$('preset').value];
    if(!p)return;
    $('rho').value=p.rho;$('viscosityMode').value='dynamic';lastViscosityType='dynamic';$('viscosity').value=p.mu;
    text('viscosityLabel','动力粘度 μ (Pa·s)'); calculate();
  }
  function viscositySwitch(previousType) {
    const now=$('viscosityMode').value, rho=number('rho');
    const old=number('viscosity');
    if(Number.isFinite(old)&&Number.isFinite(rho)&&rho>0 && previousType!==now){
      $('viscosity').value=now==='kinematic'?String(old/rho):String(old*rho);
    }
    $('viscosityLabel').innerHTML=now==='kinematic'?'运动粘度 ν <small>m²/s</small>':'动力粘度 μ <small>Pa·s</small>';
    calculate();
  }
  function chart(result) {
    const a=result.layers, n=a.length, W=760,H=240,left=76,right=16,top=16,bottom=37;
    const width=W-left-right, height=H-top-bottom;
    const min=Math.min(a[0].thickness,result.T)*0.75, max=result.T*1.3;
    const lo=Math.log10(min),hi=Math.log10(max);
    const y=v=>top+height*(hi-Math.log10(Math.max(v,min)))/(hi-lo);
    const x=i=>left+(i+.5)*width/n;
    const bw=Math.max(1,width/n*.69);
    let s='<defs><linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6ce9d9"/><stop offset="1" stop-color="#568bed"/></linearGradient></defs>';
    for(let t=0;t<5;t++){
      const val=Math.pow(10,lo+(hi-lo)*t/4),yy=y(val);
      s+=`<line class="gridline" x1="${left}" y1="${yy.toFixed(1)}" x2="${W-right}" y2="${yy.toFixed(1)}"/>`;
      s+=`<text class="axislabel" x="${left-8}" y="${(yy+4).toFixed(1)}" text-anchor="end">${format(val*1000,3)} mm</text>`;
    }
    let pts='';
    a.forEach((z,i)=>{
      const xx=x(i),yy=y(z.thickness),ybase=y(min);
      s+=`<rect class="bar" x="${(xx-bw/2).toFixed(1)}" y="${yy.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(0,ybase-yy).toFixed(1)}"/>`;
      pts+=`${xx.toFixed(1)},${y(z.cumulative).toFixed(1)} `;
    });
    s+=`<polyline class="cumline" points="${pts}"/>`;
    const endpoint=a[a.length-1];
    s+=`<circle class="cum-end" cx="${x(n-1).toFixed(1)}" cy="${y(endpoint.cumulative).toFixed(1)}" r="4"/>`;
    s+=`<text class="axislabel" x="${left}" y="${H-12}">第 1 层</text>`;
    s+=`<text class="axislabel" x="${W-right}" y="${H-12}" text-anchor="end">第 ${n} 层</text>`;
    $('chart').innerHTML=s;
  }
  function render(result) {
    latest=result;window.PrismLayerLatest={N:result.N,r:result.r,w:result.w,T:result.T,yp:result.yp,layers:result.layers}; const f=result.flow;
    text('outW',lengthHuman(result.w));text('outWm',scientific(result.w,9)+' m');
    text('outT',lengthHuman(result.T));text('outTm',scientific(result.T,9)+' m');
    text('outN',result.N);text('outR',format(result.r,9));
    text('outRe',format(f.Re,5));text('outCf',format(f.Cf,6));
    text('outUtau',format(f.utau,6)+' m/s');
    text('outYp',format(result.predictedYplus,5)+'（预测）');
    text('outDelta',f.delta===null?'不适用':lengthHuman(f.delta));
    text('outLast',lengthHuman(result.last));
    text('outRatio',f.delta===null?'不适用':format(result.T/f.delta,5));
    text('outCoreRatio',result.coreRatio===null?'未提供':format(result.coreRatio,5));
    text('correlation','关联式：'+f.correlation+'；局部参考位置 x='+format(f.x,5)+' m，摩擦剪应力='+format(f.tau,5)+' Pa。');
    const extras=[];
    if(result.targetT!==null) extras.push('目标 T='+lengthHuman(result.targetT)+'，计算得到 T='+lengthHuman(result.T));
    if(result.calibration) extras.push('按实测比例校准：w旧='+lengthHuman(result.calibration.oldW)+'，比例因子='+format(result.calibration.scale,6)+'，w新='+lengthHuman(result.w)+'。这不是重新求解后的实际 y+。');
    if(result.cfBounds && result.input.flow==='transition' && !result.input.manualCf && f.geometry!=='pipe')
      extras.push('层流 / 全湍流局部首层厚度参考范围：'+lengthHuman(result.cfBounds.turbulentW)+' – '+lengthHuman(result.cfBounds.laminarW)+'（两种模型端点，不代表可信的转捩预测区间）。');
    text('extraInfo',extras.join(' · '));
    const box=$('warnings'); box.replaceChildren();
    for(const item of result.warnings){
      const d=document.createElement('div'); d.className='warning '+(item.level==='danger'?'danger':item.level==='info'?'info':'');
      d.textContent=(item.level==='danger'?'✖ ':item.level==='warning'?'⚠ ':'ℹ ')+item.text;
      box.appendChild(d);
    }
    chart(result);
    const table=$('layerTable'); table.replaceChildren();
    for(const z of result.layers.slice(0,100)){
      const tr=document.createElement('tr');
      for(const value of [z.i,(z.thickness*1000).toExponential(6),(z.cumulative*1000).toExponential(6),format(z.estimatedCenterYplus,5)]){
        const td=document.createElement('td'); td.textContent=String(value);tr.appendChild(td);
      }
      table.appendChild(tr);
    }
    text('standardSummary',`Number of Prism Layers = ${result.N}\nPrism Layer Stretching = ${format(result.r,10)}\nPrism Layer Total Thickness (Absolute) = ${scientific(result.T,9)} m\n首层厚度（由上述参数推得）≈ ${scientific(result.w,9)} m`);
    text('advancedSummary',`Stretching Function = Geometric Progression\nDistribution Mode = Wall Thickness\n目标 Near Wall Thickness = ${scientific(result.w,9)} m\nNumber of Layers = ${result.N}\n推导总厚度 T ≈ ${scientific(result.T,9)} m\n推导增长率 r ≈ ${format(result.r,10)}\n※ 实际可编辑字段请按本机版本的当前模式核对`);
    document.dispatchEvent(new CustomEvent('prism:result',{detail:{N:result.N,r:result.r,w:result.w,T:result.T,yp:result.yp,layers:result.layers}}));
  }
  function calculate() {
    try {
      render(core.compute(values()));$('error').hidden=true;
    } catch(err){
      latest=null;window.PrismLayerLatest=null;document.dispatchEvent(new CustomEvent('prism:error'));$('error').hidden=false;text('error',err.message || String(err));
      ['outW','outT','outN','outR','outRe','outCf','outUtau','outYp','outDelta','outLast','outRatio','outCoreRatio'].forEach(id=>text(id,'—'));
      ['outWm','outTm','correlation','extraInfo','standardSummary','advancedSummary'].forEach(id=>text(id,''));
      $('warnings').replaceChildren();$('chart').replaceChildren();$('layerTable').replaceChildren();
    }
  }
  async function copySummary(){
    if(!latest){notify('请先输入有效参数');return;}
    const r=latest,f=r.flow;
    const msg=`【Prism Layer Studio v2.3】\n模型：${f.correlation}\nRe=${format(f.Re,8)}, Cf=${format(f.Cf,8)}, uτ=${scientific(f.utau)} m/s\n目标 y+=${r.yp}；预测首层 y+=${format(r.predictedYplus,8)}\nN=${r.N}, r=${format(r.r,10)}\nw=${scientific(r.w,9)} m\nT=${scientific(r.T,9)} m\n末层=${scientific(r.last,9)} m\n\n标准 Prism Layer Mesher: Number of Layers / Stretching / Total Thickness\nAdvancing Layer Mesher: Geometric Progression + Wall Thickness 分布模式\n注意：预测 y+ 不代表 CFD 实测；请检查局部 Wall Y+ 和实际网格质量。`;
    try{await navigator.clipboard.writeText(msg); notify('设置摘要已复制');}
    catch(_){const ta=document.createElement('textarea');ta.value=msg;document.body.appendChild(ta);ta.select();const ok=document.execCommand('copy');ta.remove();notify(ok?'设置摘要已复制':'复制失败，请使用导出功能');}
  }
  function download(name,contents,mime){
    const u=URL.createObjectURL(new Blob([contents],{type:mime}));const a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);
    notify(name+' 已导出');
  }
  function exportCsv(){
    if(!latest)return notify('无可导出的结果');
    let csv='\ufeff层号,单层厚度(m),累计厚度(m),预测质心y+,预测层外缘y+\n';
    for(const z of latest.layers)csv+=[z.i,scientific(z.thickness),scientific(z.cumulative),format(z.estimatedCenterYplus,9),format(z.estimatedOuterYplus,9)].join(',')+'\n';
    download('prism-layer-studio-layers.csv',csv,'text/csv;charset=utf-8');
  }
  function exportJson(){
    if(!latest)return notify('无可导出的结果');
    download('prism-layer-studio-result.json',JSON.stringify({version:'2.2',generatedAt:new Date().toISOString(),result:latest},null,2),'application/json;charset=utf-8');
  }
  /* Fluid material library: custom accessible dropdown backed by the original select. */
  function initFluidPicker() {
    const root=$('fluidSelect'), picker=$('fluidPicker'), native=$('preset');
    const trigger=$('fluidTrigger'), menu=$('fluidMenu');
    if (!root || !picker || !trigger || !menu) return () => {};
    const dictionary={
      custom:{title:'自定义',sub:'手动设置物性',icon:'＋',kind:'custom'},
      air25:{title:'空气',temp:'25°C',sub:'常压参考',icon:'气',kind:'gas'},
      air15:{title:'空气',temp:'15°C',sub:'常压参考',icon:'气',kind:'gas'},
      water20:{title:'水',temp:'20°C',sub:'液态',icon:'水',kind:'liquid'},
      nitrogen25:{title:'氮气',temp:'25°C',sub:'常压近似',icon:'氮',kind:'gas'},
      co225:{title:'二氧化碳',temp:'25°C',sub:'常压近似',icon:'碳',kind:'gas'}
    };
    const options=[];
    function element(tag,cls,txt){const el=document.createElement(tag);if(cls)el.className=cls;if(txt!==undefined)el.textContent=txt;return el;}
    const head=element('div','fluid-menu-top');head.append(element('strong','', '物性参数库'),element('span','', '05 MATERIALS'));menu.append(head);
    function group(title, keys) {
      const label=element('div','fluid-group-label',title); label.setAttribute('role','presentation');menu.append(label);
      for(const key of keys){
        const info=dictionary[key], p=core.PRESETS[key];
        const option=element('button','fluid-option');option.type='button';option.dataset.fluidPreset=key;
        option.id='fluid-option-'+key;option.setAttribute('role','option');option.setAttribute('aria-selected','false');option.tabIndex=-1;
        const icon=element('span','fluid-option-icon',info.icon);icon.dataset.kind=info.kind;icon.setAttribute('aria-hidden','true');
        const body=element('span','fluid-option-body');const titleRow=element('span','fluid-option-title',info.title);
        if(info.temp)titleRow.append(element('span','fluid-option-temp',info.temp));
        const meta= key==='custom'?'使用下方输入的密度与粘度':`ρ ${p.rho} kg/m³ · μ ${Number(p.mu).toExponential(2)} Pa·s`;
        body.append(titleRow,element('span','fluid-option-meta',meta));
        const check=element('span','fluid-option-check','✓');check.setAttribute('aria-hidden','true');
        option.append(icon,body,check);
        option.setAttribute('aria-label',key==='custom'?'自定义物性参数':`${info.title} ${info.temp}，密度 ${p.rho} 千克每立方米`);
        option.addEventListener('click',()=>choose(key));
        menu.append(option);options.push(option);
      }
    }
    group('自定义设置',['custom']);group('气体 / GAS',['air25','air15','nitrogen25','co225']);group('液体 / LIQUID',['water20']);
    menu.append(element('div','fluid-menu-footer','物性为参考值；请按实际温度与压力校核。'));
    function sync(){
      const value=native.value, info=dictionary[value]||dictionary.custom;
      text('fluidCurrentName',info.title+(info.temp?' '+info.temp:''));
      text('fluidCurrentMeta',value==='custom'?'手动编辑 · ρ / μ':`ρ ${core.PRESETS[value].rho} kg/m³`);
      $('fluidCurrentIcon').textContent=info.icon;
      $('fluidCurrentIcon').dataset.kind=info.kind;
      options.forEach(item=>item.setAttribute('aria-selected',String(item.dataset.fluidPreset===value)));
    }
    function close(focusTrigger){
      if(menu.hidden)return;
      menu.hidden=true;root.classList.remove('is-open');trigger.setAttribute('aria-expanded','false');
      if(focusTrigger)trigger.focus({preventScroll:true});
    }
    function show(focusItem){
      if(!menu.hidden)return;
      const box=trigger.getBoundingClientRect();
      menu.classList.toggle('opens-up',(window.innerHeight-box.bottom)<280 && box.top>290);
      menu.hidden=false;root.classList.add('is-open');trigger.setAttribute('aria-expanded','true');
      if(focusItem){const sel=options.find(opt=>opt.dataset.fluidPreset===native.value)||options[0];sel.focus({preventScroll:true});}
    }
    function choose(value){
      if(native.value!==value){native.value=value;native.dispatchEvent(new Event('change',{bubbles:true}));}
      sync();close(true);
    }
    function move(next){
      const active=options.indexOf(document.activeElement);
      const selected=options.findIndex(opt=>opt.dataset.fluidPreset===native.value);
      const index=active<0?selected:active;
      options[(index+next+options.length)%options.length].focus({preventScroll:true});
    }
    trigger.addEventListener('click',()=>menu.hidden?show(true):close(true));
    trigger.addEventListener('keydown',evt=>{
      if(evt.key==='ArrowDown'||evt.key==='ArrowUp'){
        evt.preventDefault();if(menu.hidden)show(true);else move(evt.key==='ArrowDown'?1:-1);
      }else if(evt.key==='Escape'){close(true);}
    });
    menu.addEventListener('keydown',evt=>{
      if(evt.key==='ArrowDown'||evt.key==='ArrowUp'){
        evt.preventDefault();move(evt.key==='ArrowDown'?1:-1);
      }else if(evt.key==='Home'||evt.key==='End'){
        evt.preventDefault();options[evt.key==='Home'?0:options.length-1].focus({preventScroll:true});
      }else if(evt.key==='Escape'){
        evt.preventDefault();close(true);
      }else if(evt.key==='Tab')close(false);
    });
    document.addEventListener('pointerdown',evt=>{if(!root.contains(evt.target))close(false);});
    window.addEventListener('resize',()=>close(false));
    native.addEventListener('change',sync);
    picker.hidden=false;root.classList.add('enhanced');$('presetLabel').htmlFor='fluidTrigger';sync();
    return sync;
  }
  const syncFluidPicker=initFluidPicker();
  let lastViscosityType=$('viscosityMode').value;
  $('viscosityMode').addEventListener('change',()=>{const prior=lastViscosityType;lastViscosityType=$('viscosityMode').value;viscositySwitch(prior);});
  $('preset').addEventListener('change',presetChange);
  $('geometry').addEventListener('change',()=>{geometryUpdate();calculate();});
  for(const id of ids.filter(id=>!['viscosityMode','geometry'].includes(id))) {
    $(id).addEventListener('input',()=>{if(id==='rho'||id==='viscosity'){$('preset').value='custom';syncFluidPicker();}calculate();});
    $(id).addEventListener('change',calculate);
  }
  document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{mode=button.dataset.mode;modeUpdate();calculate();}));
  $('calcButton').addEventListener('click',()=>{calculate();if(latest)notify('计算已更新');});
  $('resetButton').addEventListener('click',()=>{for(const [k,v] of Object.entries(core.DEFAULTS)){if($(k))$(k).value=v;}
    $('preset').value='air25';syncFluidPicker();mode='forward';lastViscosityType='dynamic';modeUpdate();geometryUpdate();text('viscosityLabel','动力粘度 μ (Pa·s)');calculate();notify('已恢复默认示例');});
  $('copyButton').addEventListener('click',copySummary);$('csvButton').addEventListener('click',exportCsv);$('jsonButton').addEventListener('click',exportJson);
  modeUpdate();geometryUpdate();calculate();
})();
