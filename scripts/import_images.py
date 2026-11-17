"""Import original PNG/JPEG pages without redrawing their visible text."""
import argparse,hashlib,json,shutil,subprocess,uuid
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('images',nargs='+');a=ap.parse_args();root=Path(a.root).resolve();(root/'pages').mkdir(parents=True,exist_ok=True);runtime=root/'.runtime';runtime.mkdir(exist_ok=True);binary=runtime/'ink-ocr';source=Path(__file__).with_name('ocr.swift')
 if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:subprocess.run(['swiftc',str(source),'-O','-o',str(binary)],check=True)
 docs=[];digest=hashlib.sha256()
 for i,path in enumerate(a.images):
  p=Path(path).resolve();b=p.read_bytes();digest.update(b);image=Image.open(p);w,h=image.size;suffix='.png' if image.format=='PNG' else '.jpg' if image.format=='JPEG' else None
  if suffix is None:raise ValueError('Use PNG or JPEG source images')
  name=f'p{i+1}-en{suffix}';dest=root/'pages'/name;shutil.copyfile(p,dest);ocr=json.loads(subprocess.check_output([str(binary),str(dest)],text=True));pars=[];boxes=[];docid=f'IMG{i+1:02d}'
  for j,line in enumerate(ocr['lines']):
   pid=f'{docid}-P{j+1:03d}';text=line['text'];x,y,bw,bh=line['box'];pars.append({'id':pid,'text':text,'source_shape':None,'source_paragraph':j,'ocr':True});boxes.append({'paragraphId':pid,'start':0,'end':len(text.encode('utf-16-le'))//2,'text':text,'x':x,'y':y,'w':bw,'h':bh})
  docs.append({'id':docid,'title':p.stem,'page':i+1,'en':pars,'images':{'en':{'url':'/pages/'+name,'width':w,'height':h,'boxes':boxes}},'source_image':str(p)})
 payload={'source':{'title':'Original images','url':'','modified_time':datetime.now(timezone.utc).isoformat(),'sha256':digest.hexdigest(),'kind':'image-ocr'},'documents':docs,'original_images':True}
 (root/'data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2));print('Imported',len(docs),'unchanged source images')
if __name__=='__main__':main()
