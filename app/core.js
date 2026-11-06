/* Prism Layer Studio — calculation engine (browser + Node.js), MIT License */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.PrismCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const PRESETS = {
    air25: { name: '空气 25°C（常压）', rho: 1.184, mu: 1.855e-5 },
    air15: { name: '空气 15°C（常压）', rho: 1.225, mu: 1.802e-5 },
    water20: { name: '水 20°C', rho: 998.2, mu: 1.002e-3 },
    nitrogen25: { name: '氮气 25°C（近似）', rho: 1.145, mu: 1.776e-5 },
    co225: { name: '二氧化碳 25°C（近似）', rho: 1.80, mu: 1.49e-5 }
  };
  const DEFAULTS = {
    rho: 1.184, viscosity: 1.855e-5, viscosityMode: 'dynamic',
    U: 10, length: 1, xFraction: 1, geometry: 'plate', surface: 'suction',
    flow: 'turbulent', targetYplus: 1, N: 10, r: 1.2,
    designMode: 'forward', targetTmm: 10, measuredYplus: 2,
    previousWum: 70, coreCellMm: 0, manualCf: 0
  };
  function finitePositive(v, name) {
    const n = Number(v);
    if (!Number.isFinite(n) || n <= 0) throw new Error(name + '必须为有限的正数。');
    return n;
  }
  function finiteNonnegative(v, name) {
    const n = Number(v);
    if (!Number.isFinite(n) || n < 0) throw new Error(name + '必须为有限且不小于 0 的数。');
    return n;
  }
  function geomSum(n, r) {
    if (!Number.isInteger(n) || n < 1 || n > 500) throw new Error('层数 N 必须为 1–500 的整数。');
    if (!Number.isFinite(r) || r < 1 || r > 5) throw new Error('拉伸因子 r 必须在 1–5 之间。');
    // Direct accumulation avoids cancellation when r is extremely close to 1.
    let sum = 0, term = 1;
    for (let i = 0; i < n; i++) {
      sum += term;
      if (!Number.isFinite(sum)) throw new Error('几何级数溢出：请降低 N 或 r。');
      term *= r;
    }
    return sum;
  }
  function solveN(target, w, r) {
    finitePositive(target, '目标总厚度'); finitePositive(w, '首层厚度');
    for (let n = 1; n <= 500; n++) if (w * geomSum(n, r) >= target * (1 - 1e-12)) return n;
    throw new Error('在 N≤500 的限制下无法达到目标总厚度。请调整目标或 r。');
  }
  function solveR(target, w, n) {
    finitePositive(target, '目标总厚度'); finitePositive(w, '首层厚度');
    const minimum = n * w;
    if (target < minimum * (1 - 1e-10))
      throw new Error('目标总厚度小于 N×首层厚度；r≥1 时不存在解。请减小 N 或增大目标厚度。');
    if (Math.abs(target - minimum) < Math.max(minimum, target) * 1e-10) return 1;
    if (n === 1) throw new Error('N=1 时总厚度恒为首层厚度，无法利用拉伸因子改变总厚度。');
    const totalAt = stretch => {
      try { return w * geomSum(n, stretch); }
      catch (err) { if (String(err.message).includes('溢出')) return Infinity; throw err; }
    };
    if (totalAt(5) < target) throw new Error('在 r≤5 的限制下达不到目标厚度。请调整目标或 N。');
    let lo = 1, hi = 5;
    for (let k = 0; k < 100; k++) {
      const mid = (lo + hi) / 2;
      if (totalAt(mid) >= target) hi = mid; else lo = mid;
    }
    return (lo + hi) / 2;
  }
  function fluidModel(inp, warnings) {
    const rho = finitePositive(inp.rho, '流体密度 ρ');
    const viscosity = finitePositive(inp.viscosity, '粘度');
    const mu = inp.viscosityMode === 'kinematic' ? viscosity * rho : viscosity;
    const nu = mu / rho;
    const U = finitePositive(inp.U, '速度 U');
    const length = finitePositive(inp.length, '几何长度');
    const geom = inp.geometry || 'plate';
    if (!['plate', 'pipe', 'wing'].includes(geom)) throw new Error('不支持的几何类型。');
    const xFraction = geom === 'pipe' ? 1 : finitePositive(inp.xFraction, '位置 x/L');
    if (xFraction > 1) throw new Error('位置 x/L 应在 (0, 1] 范围内。');
    const x = geom === 'pipe' ? length : length * xFraction;
    const re = rho * U * x / mu;
    if (!Number.isFinite(re) || re <= 0) throw new Error('雷诺数无效，请核对输入数量级。');
    const reGlobal = rho * U * length / mu;
    let cf, delta = null, correlation, cfLam = null, cfTurb = null;
    const manualCf = finiteNonnegative(inp.manualCf ?? 0, '手动摩擦系数 Cf');
    if (geom === 'pipe') {
      if (re < 2300) {
        cf = 16 / re; correlation = '圆管充分发展层流：Fanning Cf = 16/Re';
        warnings.push({ level: 'info', text: '圆管层流公式适用于充分发展层流；入口发展段不在模型内。' });
      } else if (re < 4000) {
        if (manualCf === 0) throw new Error('圆管流动处于 2300≤Re<4000 过渡区，不能可靠自动确定 Cf。请提供实测/外部计算的 Fanning Cf。');
        cf = manualCf; correlation = '圆管过渡区：用户指定 Fanning Cf';
        warnings.push({ level: 'warning', text: '圆管处于过渡流，使用用户输入的摩擦系数，需独立验证。' });
      } else if (re <= 1e5) {
        cf = 0.0791 * Math.pow(re, -0.25);
        correlation = '光滑圆管湍流：Blasius Fanning Cf = 0.0791/Re^0.25';
      } else {
        cf = 1 / (4 * Math.pow(0.79 * Math.log(re) - 1.64, 2));
        correlation = '光滑圆管湍流：Petukhov Darcy f/4（Fanning Cf）';
        if (re > 5e6) warnings.push({ level: 'warning', text: '管流 Re 超出所用 Petukhov 经验关联式常用范围，应使用适用的摩擦定律或实测 Cf。' });
      }
      if (manualCf > 0 && !(re >= 2300 && re < 4000)) {
        cf = manualCf; correlation = '用户输入：Fanning Cf';
      }
    } else {
      cfLam = 0.664 / Math.sqrt(re);
      cfTurb = 0.0592 * Math.pow(re, -0.2);
      const flow = inp.flow || 'turbulent';
      if (flow === 'laminar') {
        cf = cfLam; delta = 5 * x / Math.sqrt(re);
        correlation = '平板局部层流 Cf,x = 0.664/√Re_x';
      } else if (flow === 'turbulent') {
        cf = cfTurb; delta = 0.37 * x * Math.pow(re, -0.2);
        correlation = '平板局部全湍流 Cf,x = 0.0592/Re_x^0.2';
      } else if (flow === 'transition') {
        // Not a false automatic transition switch: show both local bounds.
        cf = cfTurb; delta = 0.37 * x * Math.pow(re, -0.2);
        correlation = '转捩参考：暂以全湍流局部 Cf 计算，额外显示层流/全湍流界限';
        warnings.push({ level: 'warning', text: '转捩参考不是转捩模型：局部摩擦系数与边界层厚度可能超出简单估算，必须核对仿真数据。' });
      } else throw new Error('不支持的流动状态。');
      if (manualCf > 0) { cf = manualCf; correlation = '用户输入：局部表面摩擦系数 Cf'; }
      if (geom === 'wing') {
        warnings.push({ level: 'warning', text: '翼型模式仅使用局部平板近似；吸力面/压力面选项只作为标记，不会自动考虑压力梯度、攻角、分离、曲率或转捩。' });
      }
      if (re < 1e4) warnings.push({ level: 'warning', text: '局部 Re 较低，平板经验关联式精度有限。' });
      if (delta !== null) warnings.push({ level: 'info', text: 'δ99 为简化平板估算，不能代表翼型或复杂边界层的真实厚度。' });
    }
    if (!Number.isFinite(cf) || cf <= 0) throw new Error('摩擦系数计算失败。');
    const tau = 0.5 * cf * rho * U * U;
    const utau = Math.sqrt(tau / rho);
    return { rho, mu, nu, U, length, x, xFraction, geometry: geom,
      Re: re, ReGlobal: reGlobal, Cf: cf, cfLam, cfTurb, delta, tau, utau, correlation };
  }
  function compute(raw) {
    const inp = Object.assign({}, DEFAULTS, raw || {});
    const warnings = [];
    const flow = fluidModel(inp, warnings);
    const yp = finitePositive(inp.targetYplus, '目标 y+');
    let n = Number(inp.N), r = Number(inp.r), w = 2 * yp * flow.mu / (flow.rho * flow.utau);
    const designMode = inp.designMode;
    if (designMode === 'inverseN') n = 1; // Hidden N is not an input in this mode.
    if (designMode === 'inverseR') r = 1; // Hidden r is solved rather than entered.
    if (!Number.isInteger(n) || n < 1 || n > 500) throw new Error('层数 N 必须为 1–500 的整数。');
    if (!Number.isFinite(r) || r < 1 || r > 5) throw new Error('拉伸因子 r 必须在 1–5 之间。');
    let targetT = null, calibration = null;
    if (designMode === 'inverseN') {
      targetT = finitePositive(inp.targetTmm, '目标总厚度') / 1000;
      n = solveN(targetT, w, r);
    } else if (designMode === 'inverseR') {
      targetT = finitePositive(inp.targetTmm, '目标总厚度') / 1000;
      r = solveR(targetT, w, n);
    } else if (designMode === 'calibrate') {
      const actual = finitePositive(inp.measuredYplus, '实际 Wall Y+');
      const oldW = finitePositive(inp.previousWum, '旧首层厚度') / 1e6;
      w = oldW * yp / actual;
      calibration = { actual, oldW, scale: yp / actual, predictedAfterByScaling: yp };
      warnings.push({ level: 'warning', text: '按 w_new = w_old×(y+目标/y+实测) 作一次近似校准；壁面剪应力会随重新求解变化，必须重新生成网格并求解后复测。' });
    } else if (designMode !== 'forward') throw new Error('不支持的计算模式。');
    if (!Number.isFinite(w) || w <= 0) throw new Error('首层厚度无效。');
    const T = w * geomSum(n, r);
    if (!Number.isFinite(T) || T <= 0) throw new Error('总厚度溢出或无效。');
    const layers = [], k = flow.rho * flow.utau / flow.mu;
    let cum = 0, term = w;
    for (let i = 1; i <= n; i++) {
      const yCenter = cum + term / 2;
      cum += term;
      layers.push({ i, thickness: term, cumulative: cum, estimatedCenterYplus: yCenter * k, estimatedOuterYplus: cum * k });
      term *= r;
    }
    const last = layers[n - 1].thickness;
    const predY = k * w / 2;
    if (designMode === 'calibrate') {
      warnings.push({ level: 'info', text: '校准后按经验摩擦模型回算的 y+ 与实测比例校准预测值可能不同，因为两者采用的摩擦速度来源不同。' });
    }
    if (r > 1.5) warnings.push({ level: 'warning', text: '层间增长率超过 1.5，可能造成较强的网格尺寸跳变。' });
    else if (r > 1.3) warnings.push({ level: 'info', text: '层间增长率超过常用的 1.1–1.3，建议检查质量。' });
    if (n < 5) warnings.push({ level: 'warning', text: '层数较少，可能无法充分解析壁面梯度；结合湍流模型与网格无关性检查。' });
    if (yp > 5 && yp < 30) warnings.push({ level: 'warning', text: '目标 y+ 处于常见壁面处理的敏感区间；是否允许取决于所选 wall treatment。' });
    if (yp >= 30) warnings.push({ level: 'info', text: '较高 y+ 设计通常需要与所用壁面函数及模型相匹配，不能单凭 y+ 判断精度。' });
    if (flow.delta !== null) {
      const ratio = T / flow.delta;
      if (ratio < 0.1) warnings.push({ level: 'warning', text: '棱柱层总厚度不足平板估算 δ99 的 10%；并非绝对失败，但须确认核心网格也能解析外层梯度。' });
      if (ratio > 2) warnings.push({ level: 'info', text: '棱柱层总厚度超过平板估算 δ99 的两倍，建议审查网格量与质量。' });
    } else if (T >= flow.length / 2) warnings.push({ level: 'danger', text: '管道 T≥D/2，存在两侧棱柱层干涉风险。' });
    else if (T > flow.length / 4) warnings.push({ level: 'warning', text: '管道棱柱层已占半径的 50% 以上，请检查核心区域和塌陷层。' });
    const coreCellMm = finiteNonnegative(inp.coreCellMm ?? 0, '核心网格参考尺寸');
    const coreRatio = coreCellMm ? last / (coreCellMm / 1000) : null;
    if (coreRatio !== null && (coreRatio < 0.2 || coreRatio > 2)) warnings.push({ level: 'warning', text: '末层厚度与核心单元参考尺寸相差较大，建议检查棱柱层与核心网格衔接。' });
    if (targetT !== null && designMode === 'inverseN' && T > targetT * 1.1)
      warnings.push({ level: 'info', text: '层数取整后总厚度超过目标 10%；可适当调整增长率或目标厚度。' });
    const cfBounds = flow.cfLam && flow.cfTurb ? {
      laminarW: 2 * yp * flow.mu / (flow.rho * flow.U * Math.sqrt(flow.cfLam / 2)),
      turbulentW: 2 * yp * flow.mu / (flow.rho * flow.U * Math.sqrt(flow.cfTurb / 2))
    } : null;
    return { input: inp, flow, N: n, r, w, T, targetT, yp, predictedYplus: predY,
      last, coreRatio, layers, warnings, calibration, cfBounds, mode: designMode };
  }
  return { PRESETS, DEFAULTS, geomSum, solveN, solveR, fluidModel, compute };
});
