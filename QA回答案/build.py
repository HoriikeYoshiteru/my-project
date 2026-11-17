import sys,glob,openpyxl
from openpyxl.styles import Alignment,Font
A={}
for f in sorted(glob.glob('answers_*.py')):
    ns={};exec(open(f).read(),ns);A.update(ns['A'])
wb=openpyxl.Workbook();ws=wb.active;ws.title='回答案'
ws.append(['シート','No.','回答(日本語) → N列','回答(中国語) → O列','メモ'])
for (s,n),(j,c) in A.items(): ws.append([s,n,j,c,''])
for col,w in zip('ABCDE',[14,6,70,70,30]): ws.column_dimensions[col].width=w
for row in ws.iter_rows():
    for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
for c in ws[1]: c.font=Font(bold=True)
wb.save('QA回答案_261117.xlsx');print(len(A))
