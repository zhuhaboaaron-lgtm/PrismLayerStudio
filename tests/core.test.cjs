'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('../app/core.js');
function close(actual, expected, rel=1e-9) {
  assert.ok(Math.abs(actual-expected) <= rel * Math.max(1e-30,Math.abs(expected)), `expected ${actual} ≈ ${expected}`);
}
test('default air/flat-plate run: correct local formula, wall unit, total thickness',()=>{
  const r=core.compute();
  close(r.flow.Re, 638274.9326145552);
  close(r.flow.Cf,0.0592*Math.pow(r.flow.Re,-0.2));
  close(r.w,0.00006932296515521358);
  close(r.T,0.0017995328155254406);
  close(r.predictedYplus,1);
  close(r.layers.reduce((sum,x)=>sum+x.thickness,0),r.T);
});
test('viscosity: kinematic and dynamic conversions identical',()=>{
  const d=core.compute();
  const k=core.compute({viscosityMode:'kinematic',viscosity:1.855e-5/1.184});
  close(d.w,k.w);close(d.flow.Re,k.flow.Re);
});
test('r=1 geometric layers and N=1',()=>{
  const r=core.compute({N:1,r:1});close(r.T,r.w);
  close(core.geomSum(300,1+1e-13),300+300*299/2*1e-13,1e-12);
});
test('inverse N: smallest integer meeting target total thickness',()=>{
  const r=core.compute({designMode:'inverseN',targetTmm:25,r:1.2,N:NaN});
  assert.ok(r.T>=0.025);
  if(r.N>1)assert.ok(r.w*core.geomSum(r.N-1,r.r)<0.025);
});
test('inverse r: bisection returns exact target with N given',()=>{
  const r=core.compute({designMode:'inverseR',targetTmm:10,N:12,r:NaN});
  close(r.T,0.01,1e-10);assert.ok(r.r>1);
});
test('inverse r: rejects impossible target',()=>{
  assert.throws(()=>core.compute({designMode:'inverseR',targetTmm:0.01,N:300}),/小于 N×首层厚度/);
});
test('pipe laminar uses Fanning Cf=16/Re, not Blasius',()=>{
  const r=core.compute({geometry:'pipe',rho:1,viscosity:0.001,U:1,length:1});
  close(r.flow.Re,1000);close(r.flow.Cf,0.016);
});
test('pipe turbulent uses Blasius then high-Re Petukhov',()=>{
  const a=core.compute({geometry:'pipe',rho:1,viscosity:1e-3,U:50,length:1});
  close(a.flow.Cf,0.0791*Math.pow(50000,-.25));
  const b=core.compute({geometry:'pipe',rho:1,viscosity:1e-4,U:100,length:1});
  close(b.flow.Cf,1/(4*(0.79*Math.log(1e6)-1.64)**2));
});
test('pipe transitional model requires external Cf',()=>{
  const opts={geometry:'pipe',rho:1,viscosity:0.001,U:3,length:1};
  assert.throws(()=>core.compute(opts),/过渡区/);
  const r=core.compute({...opts,manualCf:0.012});close(r.flow.Cf,0.012);
});
test('wing x/c uses local position, rather than entire chord',()=>{
  const r=core.compute({geometry:'wing',length:0.4,xFraction:0.25});
  close(r.flow.x,0.1);close(r.flow.Re,1.184*10*.1/1.855e-5);
  assert.ok(r.warnings.some(w=>w.text.includes('局部平板')));
});
test('transition reference retains laminar/turbulent estimates and warning',()=>{
  const r=core.compute({flow:'transition'});
  assert.ok(r.cfBounds.laminarW>r.cfBounds.turbulentW);
  assert.ok(r.warnings.some(w=>w.text.includes('转捩参考不是转捩模型')));
});
test('calibration: measured y+ correction scales previous w, not actual CFD',()=>{
  const r=core.compute({designMode:'calibrate',previousWum:80,measuredYplus:4,targetYplus:1});
  close(r.w,20e-6);close(r.calibration.scale,.25);
  assert.ok(r.warnings.some(w=>w.text.includes('重新求解')));
});
test('input safety: invalid and overflow parameters are rejected',()=>{
  assert.throws(()=>core.compute({rho:0}),/密度/);
  assert.throws(()=>core.compute({N:3.2}),/整数/);
  assert.throws(()=>core.compute({r:7}),/1–5/);
  assert.throws(()=>core.compute({geometry:'wing',xFraction:1.1}),/位置/);
  assert.throws(()=>core.geomSum(500,5),/溢出/);
});
