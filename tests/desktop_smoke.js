/* Executed inside the REAL packaged WebView2 page only when explicitly enabled.
   No application UI, physics, or browser source is modified by this test. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const close = (actual, expected, message, relative = 1e-8) =>
    assert(Math.abs(actual - expected) <= relative * Math.max(1e-30, Math.abs(expected)), `${message}: ${actual} / ${expected}`);
  const report = {
    suite: 'Prism Layer Studio desktop WebView2 integration',
    startedAt: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: location.href,
    devicePixelRatio,
    viewport: {width: innerWidth, height: innerHeight},
    dpiMethod: 'WebView2 force-device-scale-factor; system multi-monitor DPI transitions are not claimed',
    tests: [], layouts: [], errors: []
  };
  window.addEventListener('error', event => report.errors.push(String(event.message)));
  window.addEventListener('unhandledrejection', event => report.errors.push(String(event.reason)));
  const api = window.pywebview.api;
  const set = (id, value, event = 'input') => {
    $(id).value = String(value); $(id).dispatchEvent(new Event(event, {bubbles: true}));
  };
  const reset = () => $('resetButton').click();
  const latest = () => {
    assert($('error').hidden, $('error').textContent);
    assert(window.PrismLayerLatest, 'calculation did not produce a model');
    return window.PrismLayerLatest;
  };
  const mode = value => document.querySelector(`[data-mode="${value}"]`).click();
  const run = async (name, action) => {
    const started = performance.now();
    try {
      const detail = await action();
      report.tests.push({name, passed: true, milliseconds: Math.round(performance.now() - started), detail});
    } catch (error) {
      report.tests.push({name, passed: false, milliseconds: Math.round(performance.now() - started), error: String(error.stack || error)});
    }
  };
  const waitFor = async (predicate, description, timeout = 10000) => {
    const start = performance.now();
    while (!(await predicate())) {
      if (performance.now() - start > timeout) throw new Error(`Timed out: ${description}`);
      await pause(100);
    }
  };
  const keyboard = (element, key) => element.dispatchEvent(new KeyboardEvent('keydown', {key, bubbles: true, cancelable: true}));

  (async () => {
    await pause(350);
    await run('v2.6 entry, local resources, initial render and numerical baseline', () => {
      assert(location.hostname === '127.0.0.1', 'page was not served exclusively over loopback');
      assert(document.querySelector('.status-right b').textContent === 'v2.6', 'not the official v2.6 entry');
      assert($('fluidSelect').classList.contains('enhanced'), 'v2.6 material picker did not initialize');
      const expected = window.PrismCore.compute(), result = latest();
      close(result.w, 0.00006932296515521358, 'default first thickness');
      close(result.T, 0.0017995328155254406, 'default total thickness');
      close(result.w, expected.w, 'UI/core agreement');
      assert($('layerTable').children.length === 10, 'layer table missing');
      assert(document.querySelectorAll('#chart .bar').length === 10, 'chart did not render');
      const resources = performance.getEntriesByType('resource').map(entry => entry.name);
      assert(resources.every(name => new URL(name).origin === location.origin || name.startsWith('data:')), 'remote network resource requested');
      return {resources, bodyFont: getComputedStyle(document.body).fontFamily};
    });
    await run('material menu mouse selection, close and automatic property refresh', () => {
      reset();
      const before = latest().w;
      $('fluidTrigger').click();
      assert(!$('fluidMenu').hidden && $('fluidTrigger').getAttribute('aria-expanded') === 'true', 'menu failed to open');
      document.querySelector('[data-fluid-preset="water20"]').click();
      assert($('fluidMenu').hidden && $('preset').value === 'water20', 'selection did not close menu');
      close(Number($('rho').value), 998.2, 'water density');
      close(Number($('viscosity').value), 0.001002, 'water viscosity');
      close(latest().w, window.PrismCore.compute({rho:998.2,viscosity:0.001002}).w, 'water thickness');
      assert(latest().w !== before && $('fluidCurrentName').textContent.includes('水'), 'preset did not refresh outputs');
    });
    await run('material menu keyboard arrows, Home/End, Escape and outside close', () => {
      reset(); $('fluidTrigger').focus(); keyboard($('fluidTrigger'), 'ArrowDown');
      assert(!$('fluidMenu').hidden, 'ArrowDown did not open menu');
      keyboard(document.activeElement, 'End');
      assert(document.activeElement.dataset.fluidPreset === 'water20', 'End did not reach water');
      keyboard(document.activeElement, 'Home');
      assert(document.activeElement.dataset.fluidPreset === 'custom', 'Home did not reach custom');
      keyboard(document.activeElement, 'ArrowDown');
      assert(document.activeElement.dataset.fluidPreset === 'air25', 'arrow navigation incorrect');
      keyboard(document.activeElement, 'Escape');
      assert($('fluidMenu').hidden && document.activeElement === $('fluidTrigger'), 'Escape did not restore focus');
      $('fluidTrigger').click();
      document.body.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true}));
      assert($('fluidMenu').hidden, 'outside click did not close menu');
    });
    await run('manual properties become custom, physical viscosity conversion preserved', () => {
      reset(); set('rho', 1.3);
      assert($('preset').value === 'custom' && $('fluidCurrentName').textContent === '自定义', 'custom property state incorrect');
      const before = latest().w;
      set('viscosityMode', 'kinematic', 'change');
      close(Number($('viscosity').value), 1.855e-5/1.3, 'kinematic conversion');
      close(latest().w, before, 'conversion changed physical calculation');
      set('viscosityMode', 'dynamic', 'change'); close(latest().w, before, 'reverse conversion');
    });
    await run('forward mode refreshes immediately and updates real hero layers', () => {
      reset(); set('targetYplus', 2); set('N', 12); set('r', 1.15);
      const expected = window.PrismCore.compute({targetYplus:2,N:12,r:1.15}), result = latest();
      close(result.w, expected.w, 'forward w'); close(result.T, expected.T, 'forward T');
      assert(result.N === 12 && document.querySelectorAll('#heroMeshBase [data-band]').length === 12, 'hero did not rebuild from actual output');
    });
    await run('inverse layer count gives the smallest integer reaching thickness', () => {
      reset(); mode('inverseN'); set('targetTmm',25);
      const result = latest(); assert($('nRow').hidden && !$('targetTRow').hidden, 'inverse N field state');
      assert(result.T >= 0.025 && result.w * window.PrismCore.geomSum(result.N-1,result.r) < 0.025, 'inverse N minimality');
    });
    await run('inverse stretch mode reaches target thickness', () => {
      reset(); set('N',12); mode('inverseR'); set('targetTmm',10);
      const result = latest(); assert($('rRow').hidden, 'solved r field remains editable');
      close(result.T,0.01,'inverse r total',1e-10); assert(result.r > 1 && result.r <= 5, 'inverse r range');
    });
    await run('measured Wall Y+ calibration retains the original scaling model', () => {
      reset(); mode('calibrate'); set('previousWum',80); set('measuredYplus',4);
      assert(!$('calibrationFields').hidden, 'calibration inputs hidden');
      close(latest().w,20e-6,'measured calibration');
      assert($('warnings').textContent.includes('重新求解'), 'calibration physical caveat lost');
    });
    await run('wing local x/c, both surface labels and laminar/transition modes', () => {
      reset(); set('geometry','wing','change'); set('length',0.4); set('xFraction',0.25);
      assert(!$('sideRow').hidden && $('lengthLabel').textContent.includes('翼型'), 'wing UI missing');
      const before = latest().w; set('surface','pressure','change'); close(latest().w,before,'surface is label only');
      set('flow','laminar','change');
      close(latest().w,window.PrismCore.compute({geometry:'wing',length:0.4,xFraction:0.25,flow:'laminar'}).w,'local laminar model');
      set('flow','transition','change'); latest();
      assert($('warnings').textContent.includes('转捩参考不是转捩模型'), 'transition caution missing');
    });
    await run('pipe Fanning laminar, transitional validation and manual Cf', () => {
      reset(); set('geometry','pipe','change'); set('rho',1); set('viscosity',0.001); set('U',1); set('length',1);
      close(latest().w,window.PrismCore.compute({geometry:'pipe',rho:1,viscosity:0.001,U:1,length:1}).w,'pipe laminar');
      assert($('outerFields').hidden, 'outer flow fields shown for pipe');
      set('U',3); assert(!$('error').hidden && window.PrismLayerLatest === null, 'pipe transition silently accepted');
      set('manualCf',0.012); latest();
    });
    await run('invalid input clears stale results and recovers after correction', () => {
      reset(); set('rho',0);
      assert(!$('error').hidden && window.PrismLayerLatest === null && $('outW').textContent === '—', 'stale calculation displayed');
      assert($('heroInteractive').classList.contains('hero-invalid'), 'invalid hero state missing');
      set('rho',1.184); latest();
      assert(!$('heroInteractive').classList.contains('hero-invalid'), 'hero did not recover');
    });
    await run('mesh pointer follow, selection, keyboard and animation pause/resume', async () => {
      reset(); window.scrollTo({top:0,left:0,behavior:'instant'}); await pause(200);
      const scene = $('heroScene'), rect = scene.getBoundingClientRect();
      scene.dispatchEvent(new PointerEvent('pointerenter',{bubbles:true}));
      scene.dispatchEvent(new PointerEvent('pointermove',{clientX:rect.left+rect.width*.75,clientY:rect.top+rect.height*.3,bubbles:true}));
      const coordinates=$('sceneCoordinates').textContent;
      const pointerX=Number(coordinates.match(/X\s+([\d.]+)/)?.[1]);
      assert(Math.abs(pointerX-.75)<.02, 'pointer coordinates not updated: '+coordinates);
      await pause(400);
      assert(Number($('heroReveal').getAttribute('cx')) > 310, 'mouse reveal did not follow pointer');
      scene.dispatchEvent(new MouseEvent('click',{clientX:rect.left+rect.width*.5,clientY:rect.top+rect.height*.5,bubbles:true}));
      assert($('heroProbe').children.length > 0 && $('heroInspectionValue').textContent.includes('预测'), 'click probe missing');
      const selected = $('heroInspectionIndex').textContent;
      $('heroInteractive').focus({preventScroll:true}); keyboard($('heroInteractive'),'ArrowRight');
      assert($('heroInspectionIndex').textContent !== selected, 'keyboard layer selection did not change');
      const prior = $('heroMotionToggle').getAttribute('aria-pressed'); $('heroMotionToggle').click();
      assert($('heroMotionToggle').getAttribute('aria-pressed') !== prior, 'pause toggle failed');
      $('heroMotionToggle').click(); assert($('heroMotionToggle').getAttribute('aria-pressed') === prior, 'resume toggle failed');
    });
    await run('collapsed equations expand with native offline MathML and all 15 formulas', async () => {
      const details = $('mathSection'); assert(!details.open, 'math panel not collapsed initially');
      details.querySelector('summary').click(); await pause(250);
      assert(details.open, 'equations did not expand');
      const equations = [...document.querySelectorAll('.equation')]; assert(equations.length === 15,'formula count changed');
      assert(typeof MathMLElement !== 'undefined','WebView2 does not implement MathML Core');
      const maths = [...document.querySelectorAll('.equation math')];
      assert(maths.every(node => node.namespaceURI === 'http://www.w3.org/1998/Math/MathML' && node.getBoundingClientRect().height > 0),'MathML did not render');
      const fractions = [...document.querySelectorAll('mfrac')]; assert(fractions.length > 0 && fractions.every(node=>node.getBoundingClientRect().height>0),'fractions did not render');
      return {equations:equations.length,mathElements:maths.length,font:getComputedStyle(maths[0]).fontFamily};
    });
    await run('CSV and JSON buttons save real Unicode-path UTF-8 files through native bridge', async () => {
      reset(); $('csvButton').click();
      await waitFor(async () => (await api.smoke_status()).exports.some(file => file.name.endsWith('.csv')),'CSV save');
      $('jsonButton').click();
      await waitFor(async () => (await api.smoke_status()).exports.some(file => file.name.endsWith('.json')),'JSON save');
      return (await api.smoke_status()).exports;
    });
    await run('copy button reaches the Windows clipboard with the 2.6.0 release identifier', async () => {
      $('copyButton').click();
      await waitFor(async () => (await api.smoke_status()).clipboard.includes('Prism Layer Studio v2.6.0'),'native clipboard write');
      const copied = (await api.smoke_status()).clipboard;
      assert(copied.includes('N=10') && copied.includes('预测 y+'),'clipboard content incomplete');
      return {characters:copied.length};
    });
    await run('actual native resize at multiple widths has no horizontal overflow or input clipping', async () => {
      for (const [width,height] of [[900,680],[1100,800],[1440,960]]) {
        await api.smoke_set_window('resize',width,height); await pause(400);
        const rootWidth = document.documentElement.clientWidth;
        const violations = [];
        if (document.documentElement.scrollWidth > rootWidth + 2) violations.push('document horizontal overflow');
        for (const element of document.querySelectorAll('.field input,.field select,.fluid-trigger,.actions button')) {
          if (!element.getClientRects().length) continue;
          const rect = element.getBoundingClientRect();
          if (rect.left < -2 || rect.right > rootWidth+2 || rect.width < 30) violations.push(element.id || element.className);
        }
        const details = $('mathSection'); details.open = true;
        for (const element of document.querySelectorAll('.equation math')) {
          const a=element.getBoundingClientRect(), b=element.closest('.formula-card').getBoundingClientRect();
          if(a.left < b.left-2 || a.right > b.right+2) violations.push('MathML clipped: '+element.closest('.equation').getAttribute('aria-label'));
        }
        const layout = {requested:{width,height},actual:{width:innerWidth,height:innerHeight},devicePixelRatio,scrollWidth:document.documentElement.scrollWidth,violations};
        report.layouts.push(layout); assert(violations.length === 0,JSON.stringify(layout));
      }
    });
    await run('native maximize, minimize and restore keep the calculation intact', async () => {
      const value=latest().w;
      for(const action of ['maximize','restore','minimize','restore']) {await api.smoke_set_window(action,0,0); await pause(250);}
      close(latest().w,value,'window lifecycle changed calculation');
    });
    await run('no remote resources and no uncaught JavaScript errors after all interactions', () => {
      const remote = performance.getEntriesByType('resource').map(entry=>entry.name).filter(name => !name.startsWith(location.origin) && !name.startsWith('data:') && !name.startsWith('blob:'));
      assert(remote.length===0,'remote resources: '+remote.join(', ')); assert(report.errors.length===0,report.errors.join('\n'));
    });
    await run('offline simulation: application CSP actively rejects a remote API request', async () => {
      let blocked = false, violation = null;
      const listener = event => {
        if (event.blockedURI.includes('prism-offline-probe.invalid')) violation = {blockedURI:event.blockedURI,directive:event.effectiveDirective};
      };
      document.addEventListener('securitypolicyviolation',listener);
      try {await fetch('https://prism-offline-probe.invalid/test',{cache:'no-store'});} catch (_) {blocked=true;}
      await pause(100); document.removeEventListener('securitypolicyviolation',listener);
      assert(blocked && violation && violation.directive==='connect-src','remote request was not rejected by the application security policy');
      report.offlineSimulation={remoteApiBlocked:true,violation,physicalNetworkDisconnected:false,method:'CSP network isolation; test driver also denies non-loopback DNS in WebView2'};
      return report.offlineSimulation;
    });
    report.finishedAt=new Date().toISOString(); report.passed=report.tests.every(test=>test.passed);
    await api.smoke_complete(JSON.stringify(report));
  })().catch(async error => {
    report.passed=false; report.fatal=String(error.stack||error); report.finishedAt=new Date().toISOString();
    await api.smoke_complete(JSON.stringify(report));
  });
  return 'desktop smoke started';
})();
