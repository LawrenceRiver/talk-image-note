const {test}=require('node:test');const assert=require('node:assert/strict');const C=require('../assets/app/cards.js');
const bounds={x:0,y:0,w:500,h:400};
test('moving into another frame leaves the requested gap',()=>{const other={x:150,y:80,w:100,h:80},q=C.avoid({x:140,y:90,w:100,h:50},[other],bounds,7);assert.equal(C.overlaps(q,other,6.9),false);assert.ok(q.x>=0&&q.y>=0)});
test('collision avoidance respects an asymmetric cropped canvas',()=>{const b={x:-100,y:-40,w:450,h:300},q=C.avoid({x:-120,y:-80,w:100,h:50},[],b);assert.equal(q.x,-100);assert.equal(q.y,-40)});
test('resize cannot cover multiple neighbours',()=>{const others=[{x:50,y:50,w:90,h:70},{x:150,y:50,w:90,h:70}],q=C.avoid({x:80,y:60,w:200,h:100},others,bounds,7);assert.ok(others.every(o=>!C.overlaps(q,o,6.9)))});
test('frames may approach to half a pixel',()=>{const other={x:100,y:100,w:100,h:50},q=C.avoid({x:100,y:149.8,w:100,h:30},[other],bounds,.5);assert.equal(q.y,150.5)});
test('width snap waits for sustained hover and cancels after leaving',()=>{let queued,clears=0,ready=[],cancelled=false;const hover=C.dwell(id=>ready.push(id),()=>clears++,650,fn=>{queued=fn;cancelled=false;return 1},()=>{cancelled=true});hover.hover('red');assert.deepEqual(ready,[]);queued();assert.deepEqual(ready,['red']);hover.hover('blue');hover.clear();assert.equal(cancelled,true);assert.ok(clears>=3)});
test('unchanged target does not reset dwell timer',()=>{let schedules=0;const hover=C.dwell(()=>{},()=>{},650,()=>++schedules,()=>{});hover.hover('red');hover.hover('red');assert.equal(schedules,1)});
