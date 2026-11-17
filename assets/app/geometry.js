/* Gestures use normalized source-image coordinates, independent of zoom and canvas. */
(function(root){
const bounds=ps=>{const xs=ps.map(p=>p[0]),ys=ps.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys);return {x,y,w:Math.max(...xs)-x,h:Math.max(...ys)-y}};
const clip=b=>{const x=Math.max(0,b.x),y=Math.max(0,b.y);return {x,y,w:Math.max(0,Math.min(1,b.x+b.w)-x),h:Math.max(0,Math.min(1,b.y+b.h)-y)}};
const nearest=(p,ws)=>ws.map(w=>({w,d:Math.hypot(Math.max(w.x-p[0],0,p[0]-w.x-w.w),Math.max(w.y-p[1],0,p[1]-w.y-w.h)*1.414)})).sort((a,b)=>a.d-b.d)[0];
function endpointWord(p,ws,side='start'){return ws.map(w=>({w,d:Math.hypot((side==='end'?w.x+w.w:w.x)-p[0],(w.y+w.h/2-p[1])*4)})).sort((a,b)=>a.d-b.d)[0]?.w}
function between(a,b,ws){if(a.paragraphId!==b.paragraphId)return [];const l=Math.min(a.start,b.start),r=Math.max(a.end,b.end);return ws.filter(w=>w.paragraphId===a.paragraphId&&w.start<r&&w.end>l).sort((a,b)=>a.start-b.start)}
function interpret(ps,ws){const b=bounds(ps),m=[b.x+b.w/2,b.y+b.h/2];if(b.w<.025&&b.h>.018){const n=nearest(m,ws);if(n&&n.d<.055)return {kind:'endpoint',word:endpointWord(m,ws),point:m,words:[]}}
 if(b.h<.018&&b.w>.012){const candidates=ws.filter(w=>w.x+w.w>b.x&&w.x<b.x+b.w).map(w=>({w,d:Math.abs(w.y+w.h-m[1])})).sort((a,b)=>a.d-b.d);if(!candidates.length||candidates[0].d>.025)return {kind:'none',words:[]};const seed=candidates[0].w;return {kind:'underline',words:candidates.filter(q=>q.w.paragraphId===seed.paragraphId&&Math.abs(q.w.y-seed.y)<Math.max(.003,seed.h*.45)&&q.d<.025).map(q=>q.w).sort((a,b)=>a.start-b.start)}}
 const hits=ws.filter(w=>w.x+w.w/2>=b.x-.004&&w.x+w.w/2<=b.x+b.w+.004&&w.y+w.h/2>=b.y-.004&&w.y+w.h/2<=b.y+b.h+.004);
 if(hits.length){const groups=new Map();for(const w of hits)groups.set(w.paragraphId,(groups.get(w.paragraphId)||0)+w.w*w.h);const id=[...groups].sort((a,b)=>b[1]-a[1])[0][0],chosen=hits.filter(w=>w.paragraphId===id).sort((a,b)=>a.start-b.start);return {kind:'box',words:between(chosen[0],chosen.at(-1),ws)}}
 const region=clip(b);return region.w>.008&&region.h>.008?{kind:'region',words:[],region}:{kind:'none',words:[]}
}
function lines(ws){const rows=[];for(const w of [...ws].sort((a,b)=>a.y-b.y||a.x-b.x)){let row=rows.find(r=>Math.abs(r.y-w.y)<Math.max(.003,w.h*.45));if(!row){row={...w};rows.push(row)}else{const right=Math.max(row.x+row.w,w.x+w.w);row.x=Math.min(row.x,w.x);row.w=right-row.x;row.h=Math.max(row.h,w.h)}}return rows}
const api={bounds,between,interpret,lines,endpointWord};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AnnotationGeometry=api;
})(typeof window==='undefined'?{}:window);
