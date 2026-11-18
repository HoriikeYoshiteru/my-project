# QA表(添付資料)のN列へ回答案を転記する。画像等を壊さないため、xlsx内のXMLを直接書き換える。
import sys,zipfile,re,glob,copy
from lxml import etree
import openpyxl
src,dst=sys.argv[1],sys.argv[2]
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
RNS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
q=lambda t:'{%s}%s'%(NS,t)
A={}
for f in glob.glob('answers_*.py'):
    ns={};exec(open(f).read(),ns);A.update({k:v[0] for k,v in ns['A'].items()})
wb=openpyxl.load_workbook(src,read_only=False)
rowmap={}
for ws in wb:
    for r in range(5,ws.max_row+1):
        no=ws.cell(r,2).value
        if no is not None: rowmap[(ws.title,no)]=r
zin=zipfile.ZipFile(src)
wbx=etree.fromstring(zin.read('xl/workbook.xml'))
rels=etree.fromstring(zin.read('xl/_rels/workbook.xml.rels'))
rid2t={r.get('Id'):r.get('Target') for r in rels}
sheetfile={s.get('name'):'xl/'+rid2t[s.get('{%s}id'%RNS)] for s in wbx.find(q('sheets'))}
styles=etree.fromstring(zin.read('xl/styles.xml'))
cx=styles.find(q('cellXfs'))
newxf={}
def wrapstyle(s):
    s=int(s or 0)
    if s in newxf: return newxf[s]
    xf=cx[s]; al=xf.find(q('alignment'))
    if al is not None and al.get('wrapText')=='1':
        newxf[s]=s; return s
    n=copy.deepcopy(xf)
    a=n.find(q('alignment'))
    if a is None:
        a=etree.SubElement(n,q('alignment'))
        # alignment must precede protection/extLst
        pr=n.find(q('protection'))
        if pr is not None: n.remove(a); pr.addprevious(a)
    a.set('wrapText','1'); a.set('vertical','top')
    n.set('applyAlignment','1')
    cx.append(n); cx.set('count',str(len(cx)))
    newxf[s]=len(cx)-1; return newxf[s]
def colnum(ref):
    m=re.match(r'([A-Z]+)',ref).group(1); n=0
    for ch in m: n=n*26+ord(ch)-64
    return n
out={}; done=[]; miss=[]
bysheet={}
for (sh,no),t in A.items(): bysheet.setdefault(sh,[]).append((no,t))
for sh,items in bysheet.items():
    if sh not in sheetfile: miss.append(sh); continue
    path=sheetfile[sh]
    root=etree.fromstring(zin.read(path))
    sd=root.find(q('sheetData'))
    rows={int(r.get('r')):r for r in sd}
    for no,t in items:
        r=rowmap.get((sh,no))
        if not r or r not in rows: miss.append((sh,no)); continue
        row=rows[r]; ref='N%d'%r
        c=None
        for cc in row:
            if cc.get('r')==ref: c=cc
        old=None
        if c is not None:
            # 既存値(EDR No.4のみ追記)
            ws=wb[sh]; old=ws.cell(r,14).value
        if sh=='EDR' and no==4 and old:
            t=str(old).rstrip()+"\n-------------------------------------------------------------\n"+t
        s=c.get('s') if c is not None else None
        if c is None:
            # 列順に挿入
            c=etree.Element(q('c')); c.set('r',ref)
            pos=0
            for i,cc in enumerate(row):
                if colnum(cc.get('r'))<14: pos=i+1
            row.insert(pos,c)
            # 近隣セル(M列)のスタイルを流用
            for cc in row:
                if cc.get('r')=='M%d'%r: s=cc.get('s')
        for ch in list(c): c.remove(ch)
        for a in ('t',): 
            if a in c.attrib: del c.attrib[a]
        c.set('s',str(wrapstyle(s))); c.set('t','inlineStr')
        is_=etree.SubElement(c,q('is')); tt=etree.SubElement(is_,q('t'))
        tt.text=t; tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
        done.append((sh,no))
    out[path]=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
out['xl/styles.xml']=etree.tostring(styles,xml_declaration=True,encoding='UTF-8',standalone=True)
zout=zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=out.get(it.filename,zin.read(it.filename))
    zout.writestr(it,data)
zout.close()
print('written',len(done),'missing',miss)
