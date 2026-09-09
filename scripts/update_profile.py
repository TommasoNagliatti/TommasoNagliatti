"""Refresh factual profile visuals with standard-library Python and public GitHub data."""
import argparse,collections,datetime,html,json,os,re,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
USER='TommasoNagliatti'
def repositories():
    rows=[]
    for page in range(1,20):
        headers={'User-Agent':'TommasoNagliatti-profile','Accept':'application/vnd.github+json'}
        if os.getenv('GITHUB_TOKEN'):headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
        req=urllib.request.Request(f'https://api.github.com/users/{USER}/repos?per_page=100&page={page}',headers=headers)
        with urllib.request.urlopen(req,timeout=30) as r:chunk=json.load(r)
        rows.extend(x for x in chunk if not x['fork'] and x['name'].lower()!=USER.lower())
        if len(chunk)<100:return rows
    raise RuntimeError('Repository pagination limit reached')
def card(rows,dark,mobile=False):
    bg,fg,muted,line=('#0d1117','#e6edf3','#8b949e','#223440') if dark else ('#f6f8fa','#1f2328','#59636e','#d0d7de')
    counts=collections.Counter(x['language'] for x in rows if x.get('language'))
    top=counts.most_common(5)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="290" viewBox="0 0 900 290" role="img"><title>Public repositories by primary language</title><rect width="900" height="290" rx="14" fill="{bg}"/>',
      f'<text x="28" y="38" font-family="Arial" font-size="21" font-weight="700" fill="{fg}">Learning in public</text>',
      f'<text x="28" y="68" font-family="Arial" font-size="15" fill="{muted}">{len(rows)} public source repositories · primary language per repository</text>']
    maximum=max(counts.values(),default=1)
    for i,(language,count) in enumerate(top):
        y=103+i*29
        out += [f'<text x="28" y="{y+5}" font-family="Arial" font-size="15" fill="{fg}">{html.escape(language)}</text>',
          f'<rect x="200" y="{y-9}" width="590" height="14" rx="7" fill="{line}"/>',
          f'<rect x="200" y="{y-9}" width="{590*count/maximum:.1f}" height="14" rx="7" fill="#0891b2"/>',
          f'<text x="815" y="{y+5}" font-family="Arial" font-size="15" fill="{fg}">{count}</text>']
    unclassified=sum(not x.get('language') for x in rows)
    out += [f'<text x="28" y="269" font-family="Arial" font-size="13" fill="{muted}">Not a skill ranking · {unclassified} without a primary language · updated {datetime.date.today().isoformat()}</text></svg>']
    result=''.join(out)
    if mobile:
        result=result.replace('width="900"','width="440"').replace('viewBox="0 0 900 290"','viewBox="0 0 440 290"')
        result=result.replace('x="200"','x="185"').replace('width="590"','width="185"').replace('x="815"','x="392"')
        for count in set(counts.values()):result=result.replace(f'width="{590*count/maximum:.1f}"',f'width="{185*count/maximum:.1f}"')
        result=result.replace('public source repositories · primary language per repository','public repositories · primary language')
        result=result.replace(f'Not a skill ranking · {unclassified} without a primary language · updated ',f'{unclassified} unclassified · updated ')
    return result
def enable():
    from xml.etree import ElementTree as ET
    for name in ['snake.svg','snake-dark.svg']:
        p=ROOT/'assets/generated'/name
        if not p.is_file() or p.stat().st_size<100:raise RuntimeError('Missing snake asset')
        root=ET.parse(p).getroot()
        if not root.tag.endswith('svg'):raise RuntimeError('Invalid snake SVG')
    text='''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/generated/snake-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="./assets/generated/snake.svg" />
  <img src="./assets/generated/snake.svg" width="100%" alt="Animated snake following my GitHub contribution calendar" />
</picture>'''
    p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
    s,n=re.subn(r'(?s)(<!-- SNAKE:START -->).*?(<!-- SNAKE:END -->)',lambda m:m[1]+'\n'+text+'\n'+m[2],s)
    if n!=1:raise RuntimeError('Expected one contribution section')
    p.write_text(s,encoding='utf-8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--enable-snake',action='store_true');args=p.parse_args()
    if args.enable_snake:enable()
    else:
        rows=repositories();out=ROOT/'assets/generated';out.mkdir(parents=True,exist_ok=True)
        for dark in [False,True]:
            for mobile in [False,True]:
                name='activity'+('-mobile' if mobile else '')+('-dark' if dark else '')+'.svg'
                (out/name).write_text(card(rows,dark,mobile),encoding='utf-8')
        (out/'activity.json').write_text(json.dumps({'updated':datetime.date.today().isoformat(),'repositories':[{'name':r['name'],'language':r.get('language'),'url':r['html_url']} for r in rows]},indent=2),encoding='utf-8')
