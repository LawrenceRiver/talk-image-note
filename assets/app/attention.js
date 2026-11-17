(function(root){const colors=['#cc6d91','#739ac8','#b58ac4','#69a79c','#d39a60','#b2a350'],shapes=['dot','flower','star','petal'];
function pair(d,id){const en=d.en.find(p=>p.id===id),zh=d.zh?.find(p=>p.id===id);if(!en||!zh)return null;const ref=p=>({paragraphId:p.id,start:0,end:p.text.length,offset_unit:'utf16',quote:p.text,source_shape:p.source_shape,source_paragraph:p.source_paragraph});return {en:ref(en),zh:ref(zh)}}
function sample(a,b,size,spacing=12){const distance=Math.hypot((b[0]-a[0])*size.w,(b[1]-a[1])*size.h),n=Math.floor(distance/spacing);return Array.from({length:Math.min(n,180)},(_,i)=>{const t=(i+1)*spacing/distance;return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]})}
function style(burst,i){return {color:colors[(burst+i)%colors.length],shape:shapes[i%shapes.length]}}
const api={pair,sample,style};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AnnotationAttention=api;
})(typeof window==='undefined'?{}:window);
