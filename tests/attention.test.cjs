const test=require('node:test'),assert=require('node:assert/strict');let A;try{A=require('../assets/app/attention.js')}catch{}
test('paired references require the same verified paragraph in both languages',()=>{assert.ok(A);const d={en:[{id:'p',text:'English passage'}],zh:[{id:'p',text:'中文段落'}]};assert.equal(A.pair(d,'p').zh.quote,'中文段落');assert.equal(A.pair(d,'old'),null)});
test('drag samples have regular pixel spacing after zoom',()=>{assert.ok(A);assert.equal(A.sample([0,0],[.1,0],{w:1000,h:700},10).length,10);assert.equal(A.sample([0,0],[.1,0],{w:2000,h:1400},10).length,20)});
test('decorative patterns loop and successive bursts receive different colors',()=>{assert.ok(A);assert.equal(A.style(0,0).shape,A.style(0,4).shape);assert.notEqual(A.style(0,0).color,A.style(1,0).color)});
