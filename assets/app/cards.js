(function(root){
function slots(){const out=[],add=(x,y,w,h,ring)=>out.push({x,y,w,h,ring});
 for(const x of [.02,.3575,.695])add(x,.02,.285,.105,0);
 for(const y of [.17,.405,.64])add(.84,y,.14,.205,0);
 for(const x of [.695,.3575,.02])add(x,.88,.285,.105,0);
 for(const y of [.64,.405,.17])add(.02,y,.14,.205,0);
 add(.18,.17,.125,.205,1);for(const y of [.17,.405,.64])add(.695,y,.125,.205,1);for(const y of [.64,.405])add(.18,y,.125,.205,1);
 return out;
}
function selectionAt(word,notes){const candidates=notes.filter(n=>n.anchors?.some(a=>a.paragraphId===word.paragraphId&&a.start<=word.start&&a.end>=word.end));candidates.sort((a,b)=>a.anchors.reduce((s,a)=>s+a.end-a.start,0)-b.anchors.reduce((s,a)=>s+a.end-a.start,0));return candidates[0]?.anchors.map(a=>({...a}))||null}
function crosses(a,b){const cross=(p,q,r)=>(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]);return cross(a.from,a.to,b.from)*cross(a.from,a.to,b.to)<0&&cross(b.from,b.to,a.from)*cross(b.from,b.to,a.to)<0}
function visibleLinks(links,active,all){if(all)return links;const out=[];for(const l of [...links].sort((a,b)=>(b.id===active)-(a.id===active))){if(!out.some(p=>crosses(l,p)))out.push(l)}return out}
function overlaps(a,b,gap=.5){return a.x<b.x+b.w+gap&&a.x+a.w+gap>b.x&&a.y<b.y+b.h+gap&&a.y+a.h+gap>b.y}
function avoid(rect,others,bounds,gap=.5,fallback=rect){const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),right=bounds.x+bounds.w-rect.w,bottom=bounds.y+bounds.h-rect.h;if(right<bounds.x||bottom<bounds.y)return {...fallback};const xs=[clamp(rect.x,bounds.x,right),bounds.x,right],ys=[clamp(rect.y,bounds.y,bottom),bounds.y,bottom];for(const o of others){xs.push(clamp(o.x-rect.w-gap,bounds.x,right),clamp(o.x+o.w+gap,bounds.x,right));ys.push(clamp(o.y-rect.h-gap,bounds.y,bottom),clamp(o.y+o.h+gap,bounds.y,bottom))}let best=null,score=Infinity;for(const x of xs)for(const y of ys){const q={...rect,x,y};if(others.some(o=>overlaps(q,o,gap-.01)))continue;const distance=(x-rect.x)**2+(y-rect.y)**2;if(distance<score){best=q;score=distance}}return best||{...fallback}}
function dwell(onReady,onClear,delay=650,schedule=setTimeout,cancel=clearTimeout){let key=null,timer=null;return {hover(next){if(next===key)return;cancel(timer);onClear();key=next;if(next!==null)timer=schedule(()=>{timer=null;onReady(next)},delay)},clear(){cancel(timer);timer=null;key=null;onClear()}}}
function snapTarget(point,others){return others.find(o=>point.x>=o.x&&point.x<=o.x+o.w&&point.y>=o.y&&point.y<=o.y+o.h)||null}
function releaseAction(e,pointer){if(e.pointerId!==undefined&&e.pointerId!==pointer)return null;if(e.type==='pointercancel')return 'cancel';if(['pointerup','mouseup','lostpointercapture','blur'].includes(e.type))return 'commit';if(e.type==='pointermove'&&e.buttons===0)return 'commit';if(e.type==='visibilitychange'&&e.hidden)return 'commit';return null}
const api={slots,selectionAt,visibleLinks,avoid,overlaps,dwell,snapTarget,releaseAction};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AnnotationCards=api;
})(typeof window==='undefined'?{}:window);
