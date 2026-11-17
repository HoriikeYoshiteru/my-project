import sys,glob,openpyxl
from openpyxl.styles import Alignment,Font
A={};M={}
import os
if os.path.exists('memo_local.py'):
    ns0={};exec(open('memo_local.py').read(),ns0);M.update(ns0['MEMO'])
for f in sorted(glob.glob('answers_*.py')):
    ns={};exec(open(f).read(),ns);A.update(ns['A']);M.update(ns.get('MEMO',{}))
wb=openpyxl.Workbook();ws=wb.active;ws.title='回答案'
ws.append(['シート','No.','回答(日本語) → N列','回答(中国語) → O列','メモ'])
for (s,n),(j,c) in A.items(): ws.append([s,n,j,c,M.get((s,n),'')])
for col,w in zip('ABCDE',[14,6,70,70,30]): ws.column_dimensions[col].width=w
for row in ws.iter_rows():
    for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
for c in ws[1]: c.font=Font(bold=True)
wb.save('QA回答案_261117.xlsx')
# push用: メモ列を空にした版
for r in range(2,ws.max_row+1): ws.cell(r,5).value=''
wb.save('QA回答案_261117.xlsx')
if M:
    wb2=openpyxl.Workbook();w2=wb2.active;w2.title='根拠メモ'
    w2.append(['シート','No.','根拠メモ(ローカル専用)'])
    for (s,n),m in sorted(M.items()): w2.append([s,n,m])
    w2.column_dimensions['C'].width=120
    for row in w2.iter_rows():
        for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
    wb2.save('根拠メモ_ローカル専用.xlsx')
print(len(A))
