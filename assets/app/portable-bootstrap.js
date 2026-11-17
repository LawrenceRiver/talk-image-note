(()=>{
 const payload=JSON.parse(document.getElementById('portable-state').textContent);let draft=payload.draft;const storageKey='ink-editable-'+payload.exportId;
 try{const stored=localStorage.getItem(storageKey);if(stored)draft=JSON.parse(stored)}catch{}
 const response=(value,status=200)=>Promise.resolve(new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json'}}));
 const filename=ext=>(payload.data.documents[0]?.id||'annotations')+'-'+new Date().toISOString().replace(/[:.]/g,'-')+'.'+ext;
 window.fetch=(input,options={})=>{const path=typeof input==='string'?input:input.url;let body={};try{body=JSON.parse(options.body||'{}')}catch{}
  if(path==='/data.json')return response(payload.data);
  if(path==='/api/draft'){if(options.method==='POST'){draft=body;payload.draft=draft;try{localStorage.setItem(storageKey,JSON.stringify(draft))}catch{}}return response(options.method==='POST'?{saved:true}:draft)}
  if(path==='/api/capabilities')return response({handwriting:false,storage:'editable HTML'});
  if(path==='/api/reference')return response({saved:true,id:body.id});
  if(path==='/api/export-image')return response({saved:true,file:'download',filename:filename('png'),url:body.image});
  if(path==='/api/export-editable'){const next=structuredClone(payload);next.draft=structuredClone(draft);next.exportId=crypto.randomUUID();const clone=document.documentElement.cloneNode(true);clone.querySelector('#pages').innerHTML='';clone.querySelectorAll('#tool-hint').forEach(e=>e.remove());clone.querySelector('#portable-state').textContent=JSON.stringify(next).replace(/</g,'\\u003c');clone.querySelector('#toast').hidden=true;clone.querySelector('#copy-result').hidden=true;const html='<!doctype html>\n'+clone.outerHTML,url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));return response({saved:true,file:'download',filename:filename('html'),url})}
  return response({error:'此单文件不提供这项本机服务'},400)
 };
 document.documentElement.dataset.portable='true';
})();
