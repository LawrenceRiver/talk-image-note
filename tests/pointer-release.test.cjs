const {test}=require('node:test');const assert=require('node:assert/strict');const C=require('../assets/app/cards.js');
test('mouse is released even when the original pointerup was missed',()=>{assert.equal(C.releaseAction({type:'pointermove',pointerId:4,buttons:0},4),'commit')});
test('losing capture or window focus settles the current frame',()=>{assert.equal(C.releaseAction({type:'lostpointercapture',pointerId:4},4),'commit');assert.equal(C.releaseAction({type:'blur'},4),'commit')});
test('another pointer cannot finish this gesture',()=>{assert.equal(C.releaseAction({type:'pointerup',pointerId:8},4),null)});
test('cancellation rolls back while a normal release commits',()=>{assert.equal(C.releaseAction({type:'pointercancel',pointerId:4},4),'cancel');assert.equal(C.releaseAction({type:'pointerup',pointerId:4},4),'commit')});
test('a held pointer is not treated as released',()=>{assert.equal(C.releaseAction({type:'pointermove',pointerId:4,buttons:1},4),null)});
