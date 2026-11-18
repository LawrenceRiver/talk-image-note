import base64,copy,json,re,uuid
from pathlib import Path

def build_portable(root,data,draft,doc_id):
 root=Path(root);data=copy.deepcopy(data);draft=copy.deepcopy(draft)
 document=next((d for d in data['documents'] if d['id']==doc_id),None)
 if document is None:raise ValueError('找不到要导出的篇目')
 data['documents']=[document];draft['pageIndex']=0
 for lang,image in document['images'].items():
  path=root/image['url'].lstrip('/')
  mime='image/jpeg' if path.suffix.lower() in ('.jpg','.jpeg') else 'image/png'
  image['url']='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
  high=path.with_name(path.stem+'-export.png')
  if high.exists() and not data.get('original_images'):
   image['exportUrl']='data:image/png;base64,'+base64.b64encode(high.read_bytes()).decode()
  elif data.get('original_images'):
   image['exportUrl']=image['url']
  else:
   raise ValueError('缺少高清导出原件，请先生成300dpi页面')
 draft['annotations']=[n for n in draft.get('annotations',[]) if n['docId']==doc_id]
 draft['deletedAnnotations']=[n for n in draft.get('deletedAnnotations',[]) if n['annotation']['docId']==doc_id][:2]
 draft['undoStates']=[];draft['redoStates']=[]
 if draft.get('activeId') not in [n['id'] for n in draft['annotations']]:draft['activeId']=None
 payload={'format':'ink-voice-revise-editable-v1','exportId':uuid.uuid4().hex,'data':data,'draft':draft}
 app=root/'app';html=(app/'index.html').read_text(encoding='utf-8');html=html.replace('<link rel="stylesheet" href="/style.css">','<style>'+ (app/'style.css').read_text(encoding='utf-8')+'</style>')
 safe=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')
 bootstrap=(Path(__file__).parent.parent/'assets/app/portable-bootstrap.js').read_text(encoding='utf-8')
 head='<script id="portable-state" type="application/json">'+safe+'</script><script>'+bootstrap+'</script>'
 html=html.replace('</head>',head+'</head>')
 def inline(match):
  name=match.group(1);source=(app/name).read_text(encoding='utf-8');return '<script>'+source.replace('</script','<\\/script')+'</script>'
 html=re.sub(r'<script src="/([a-z-]+\.js)"></script>',inline,html)
 if 'src="/' in html or 'href="/' in html:raise ValueError('导出仍有外部资源路径')
 return html
