import argparse,json,urllib.request
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8847');p.add_argument('--id',required=True);p.add_argument('--text',required=True);a=p.parse_args()
r=urllib.request.Request(a.url.rstrip('/')+'/api/annotate-reference',data=json.dumps({'id':a.id,'text':a.text}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(r) as f:print(f.read().decode())
