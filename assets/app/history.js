(function(root){let sequence=0;const copy=x=>JSON.parse(JSON.stringify(x));
function remove(notes,trash,id,source,placement=null){const index=notes.findIndex(n=>n.id===id);if(index<0)return {notes,trash};const record={id:Date.now()+'-'+(++sequence),deletedAt:Date.now(),source,originalIndex:index,annotation:copy(notes[index]),placement:copy(placement)};return {notes:notes.filter(n=>n.id!==id),trash:[record,...trash].slice(0,2)}}
function restore(notes,trash,id,source){const r=trash.find(r=>r.id===id);if(!r)return {notes,trash};if(r.source!==source)return {notes,trash,error:'source'};const next=[...notes];if(!next.some(n=>n.id===r.annotation.id))next.splice(Math.min(r.originalIndex,next.length),0,copy(r.annotation));return {notes:next,trash:trash.filter(t=>t.id!==id),restored:r.annotation.id}}
function preview(trash,id,source){const r=trash.find(r=>r.id===id);return r&&r.source===source?copy(r):null}
const api={remove,restore,preview};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AnnotationHistory=api;
})(typeof window==='undefined'?{}:window);
