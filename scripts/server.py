from portable_export import build_portable
from reference_model import make_reference,annotate,reference_prompt,make_canvas_reference
import argparse,base64,json,os,re,subprocess,threading,uuid
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--port',type=int,default=8847);a=ap.parse_args();root=Path(a.root).resolve();app=root/'app';store=root/'annotations';store.mkdir(exist_ok=True);(store/'ink').mkdir(exist_ok=True);(store/'exports').mkdir(exist_ok=True);runtime=root/'.runtime';runtime.mkdir(exist_ok=True);ocr=runtime/'ink-ocr';lock=threading.Lock()
 if not ocr.exists() or ocr.stat().st_mtime < Path(__file__).with_name('ocr.swift').stat().st_mtime:
  try:subprocess.run(['swiftc',str(Path(__file__).with_name('ocr.swift')),'-O','-o',str(ocr)],check=True,timeout=90,capture_output=True)
  except Exception as e: print('OCR unavailable:',str(e),flush=True)
 def write(p,obj):
  tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2));tmp.replace(p)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,obj,status=200):
   b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
  def do_GET(self):
   path=urlparse(self.path).path
   if path=='/api/draft':
    p=store/'draft.json';return self.reply(json.loads(p.read_text()) if p.exists() else {})
   if path=='/api/capabilities':return self.reply({'handwriting':ocr.exists(),'storage':str(store)})
   routes={'/':app/'index.html','/app.js':app/'app.js','/geometry.js':app/'geometry.js','/cards.js':app/'cards.js','/history.js':app/'history.js','/attention.js':app/'attention.js','/sweep.js':app/'sweep.js','/copy-notes.js':app/'copy-notes.js','/style.css':app/'style.css','/data.json':root/'data.json'}
   p=routes.get(path)
   if re.fullmatch(r'/pages/p[0-9]+-(en|zh)(-export)?\.(png|jpg)',path):p=root/path.lstrip('/')
   if re.fullmatch(r'/exports/[A-Za-z0-9-]+\.(png|html)',path):p=root/path.lstrip('/')
   if p is None or not p.exists():return self.reply({'error':'Not found'},404)
   b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',{'html':'text/html','js':'text/javascript','css':'text/css','json':'application/json','png':'image/png','jpg':'image/jpeg'}[p.suffix[1:]]+'; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  def do_POST(self):
   origin=self.headers.get('Origin')
   if origin and urlparse(origin).netloc!=self.headers.get('Host'):return self.reply({'error':'仅接受本机工作台请求'},403)
   try:
    size=int(self.headers.get('Content-Length','0'))
    if size>(50_000_000 if urlparse(self.path).path=='/api/export-image' else 5_000_000):return self.reply({'error':'内容过大'},413)
    d=json.loads(self.rfile.read(size));path=urlparse(self.path).path
    if path=='/api/draft':
     d['deletedAnnotations']=d.get('deletedAnnotations',[])[:2]
     with lock:
      old=store/'draft.json'
      if old.exists():
       previous=json.loads(old.read_text())
       if previous.get('source',{}).get('sha256')!=d.get('source',{}).get('sha256') and previous.get('annotations'):
        history=store/'history';history.mkdir(exist_ok=True);write(history/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:5]+'.json'),previous)
      write(old,d)
     return self.reply({'saved':True})
    if path=='/api/export-editable':
     with lock:
      current=json.loads((root/'data.json').read_text());draft=json.loads((store/'draft.json').read_text());doc_id=str(d.get('docId',''));html=build_portable(root,current,draft,doc_id);directory=root/'exports';directory.mkdir(exist_ok=True);filename=doc_id+'-editable-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:5]+'.html';p=directory/filename;p.write_text(html)
     return self.reply({'saved':True,'file':str(p),'filename':filename,'url':'/exports/'+filename})
    if path=='/api/export-image':
     image=d.get('image','');doc_id=str(d.get('docId',''))
     if not re.fullmatch(r'[A-Za-z0-9-]+',doc_id) or not image.startswith('data:image/png;base64,'):raise ValueError('导出图片数据无效')
     raw=base64.b64decode(image.split(',',1)[1],validate=True)
     if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('不是有效PNG')
     directory=root/'exports';directory.mkdir(exist_ok=True);filename=doc_id+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:5]+'.png';p=directory/filename;p.write_bytes(raw);write(p.with_suffix('.json'),{'docId':doc_id,'source':d.get('source'),'annotationIds':d.get('annotationIds',[]),'imageFile':str(p)})
     return self.reply({'saved':True,'file':str(p),'filename':filename,'url':'/exports/'+filename})
    if path=='/api/ocr':
     image=d.get('image','')
     if not image.startswith('data:image/png;base64,'):return self.reply({'error':'需要PNG墨迹图'},400)
     b=base64.b64decode(image.split(',',1)[1],validate=True)
     if not b.startswith(b'\x89PNG\r\n\x1a\n'):return self.reply({'error':'不是有效PNG'},400)
     p=store/'ink'/(uuid.uuid4().hex+'.png');p.write_bytes(b)
     if not ocr.exists():return self.reply({'error':'本机手写识别不可用；墨迹已保存，可交给Codex读取','image_path':str(p)},503)
     result=subprocess.run([str(ocr),str(p)],capture_output=True,text=True,timeout=30)
     if result.returncode:return self.reply({'error':'识别未完成，墨迹已保存','image_path':str(p)},500)
     data=json.loads(result.stdout);data['image_path']=str(p);return self.reply(data)
    if path=='/api/reference':
     with lock:
      current=json.loads((root/'data.json').read_text());draft=json.loads((store/'draft.json').read_text());reference=make_reference(current,draft,d.get('id'))
      directory=store/'references';directory.mkdir(exist_ok=True);p=directory/(reference['id']+'.json');write(p,reference);write(store/'latest-reference.json',reference)
     return self.reply({'reference':reference,'file':str(p),'prompt':reference_prompt(reference,p)})
    if path=='/api/reference-image':
     identifier=str(d.get('id',''));image=d.get('image','')
     if not re.fullmatch(r'[A-Za-z0-9-]+',identifier) or not image.startswith('data:image/png;base64,'):raise ValueError('引用图片数据无效')
     raw=base64.b64decode(image.split(',',1)[1],validate=True)
     if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('不是有效PNG')
     with lock:
      p=store/'references'/(identifier+'.json');reference=json.loads(p.read_text())
      if reference.get('referencedAt')!=d.get('referencedAt'):raise ValueError('引用已经更新，请重试')
      image_file=p.with_suffix('.png');image_file.write_bytes(raw);reference['imageFile']=str(image_file);write(p,reference);latest=store/'latest-reference.json'
      if latest.exists() and json.loads(latest.read_text()).get('id')==identifier:write(latest,reference)
     return self.reply({'saved':True,'imageFile':str(image_file)})
    if path=='/api/reference-canvas':
     image=d.get('image','')
     if not image.startswith('data:image/png;base64,'):raise ValueError('全图引用需要PNG')
     raw=base64.b64decode(image.split(',',1)[1],validate=True)
     if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('全图引用不是有效PNG')
     with lock:
      current=json.loads((root/'data.json').read_text());draft=json.loads((store/'draft.json').read_text());identifier='canvas-'+uuid.uuid4().hex;reference=make_canvas_reference(current,draft,d.get('docId'),identifier);directory=store/'references';directory.mkdir(exist_ok=True);png=directory/(identifier+'.png');png.write_bytes(raw);p=directory/(identifier+'.json');reference['imageFile']=str(png);write(p,reference);write(store/'latest-reference.json',reference)
      for item in reference['annotations']:write(directory/(item['id']+'.json'),item)
     lines=['[全图引用 '+reference['docId']+'](<'+str(png)+'>)','[全图定位记录](<'+str(p)+'>)','画布ID：'+identifier]
     for ref in reference['annotations']:lines+=['',reference_prompt(ref,directory/(ref['id']+'.json'))]
     return self.reply({'reference':reference,'file':str(p),'imageFile':str(png),'prompt':'\n'.join(lines)})
    if path=='/api/annotate-reference':
     with lock:
      current=json.loads((root/'data.json').read_text());draft=json.loads((store/'draft.json').read_text());p=store/'references'/(str(d.get('id',''))+'.json') if re.fullmatch(r'[A-Za-z0-9-]+',str(d.get('id',''))) else None
      if not p or not p.exists():raise ValueError('先点击引用这处定位')
      reference=json.loads(p.read_text());updated=annotate(current,draft,reference,str(d.get('text','')),targets=d.get('targets'),focus_boxes=d.get('focusBoxes'),suggestion=d.get('suggestion'));write(store/'draft.json',updated)
     return self.reply({'saved':True,'id':reference['id'],'stage':'annotation'})
    if path=='/api/submit':
     notes=[n for n in d.get('annotations',[]) if not n.get('example') and (str(n.get('note','')).strip() or n.get('attention',{}).get('points'))]
     if not notes:return self.reply({'error':'先写下一条修改意见'},400)
     current=json.loads((root/'data.json').read_text())
     if d.get('source',{}).get('sha256')!=current['source']['sha256']:return self.reply({'error':'底稿版本已变化，请先核对旧批注的对应原文'},409)
     docs={x['id']:x for x in current['documents']}
     for note in notes:
      document=docs.get(note.get('docId'));language=note.get('lang');anchors=note.get('anchors',[])
      if not document or language not in ['en','zh'] or (not anchors and not note.get('region')):return self.reply({'error':'先把尚未绑定的批注卡片拖到对应原文，再提交'},400)
      if note.get('region'):
       r=note['region']
       if not all(isinstance(r.get(k),(int,float)) for k in ['x','y','w','h']) or r['x']<0 or r['y']<0 or r['w']<=0 or r['h']<=0 or r['x']+r['w']>1.000001 or r['y']+r['h']>1.000001:return self.reply({'error':'图片选区范围无效'},400)
       note['sourceImage']=str(root/document['images'][language]['url'].lstrip('/'))
      paragraphs={x['id']:x['text'] for x in document[language]}
      for anchor in anchors:
       text=paragraphs.get(anchor.get('paragraphId'))
       if text is None:return self.reply({'error':'批注对应段落不存在'},409)
       start,end=anchor.get('start'),anchor.get('end')
       if not isinstance(start,int) or not isinstance(end,int) or start<0 or end<=start:return self.reply({'error':'原句范围无效'},400)
       expected=text.encode('utf-16-le')[start*2:end*2].decode('utf-16-le')
       if expected!=anchor.get('quote'):return self.reply({'error':'批注原句与底稿不一致，请重新定位'},409)
      if '\n'.join(x['quote'] for x in anchors)!=note.get('quote'):return self.reply({'error':'批注引文不一致'},409)
     stamp=datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:5];p=store/'exports'/(stamp+'.json');batch={'source':d.get('source'),'submitted_at':datetime.now(timezone.utc).isoformat(),'annotations':notes};write(p,batch)
     lines=['请读取这个已正式提交的圈画批注批次，按原句定位后逐处微调。不要把示例或空白当作意见。',str(p),'']
     for i,n in enumerate(notes):
      lines += [f'【第{i+1}条｜{n["docId"]}｜{n["lang"]}】','原句：'+n.get('quote',''),'我的意见：'+n.get('note','')]
      if n.get('pairedReferences'):lines+=['中文对应：'+n['pairedReferences']['zh']['quote'],'英文对应：'+n['pairedReferences']['en']['quote']]
      if n.get('attention'):lines+=['注意点：'+json.dumps(n['attention'],ensure_ascii=False),'注意点用于定位；改法以本轮用户聊天为准。']
      if n.get('region'):lines+=['原图：'+n.get('sourceImage',''),'图片选区：'+json.dumps(n['region'],ensure_ascii=False)]
      if n.get('handwritingImage'):lines+=['手写图：'+n['handwritingImage']]
      lines+=['']
     prompt='\n'.join(lines);(store/'exports'/(stamp+'.md')).write_text(prompt);write(store/'latest-submitted.json',batch)
     return self.reply({'saved':True,'file':str(p),'count':len(notes),'prompt':prompt})
    return self.reply({'error':'Not found'},404)
   except Exception as e:return self.reply({'error':str(e)},400)
 server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);print('ANNOTATION_URL=http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()
if __name__=='__main__':main()
