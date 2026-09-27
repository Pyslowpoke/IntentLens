from pathlib import Path
import csv
import random
import sqlite3
from datetime import date,timedelta
import openpyxl

root=Path(__file__).resolve().parents[1]/"samples"
root.mkdir(exist_ok=True)
r=random.Random(20260927)

def write(name,headers,rows):
    with (root/f"{name}.csv").open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)

sales=[]
for i in range(720):
    day=date(2026,1,1)+timedelta(days=i%167)
    region=['华东','华南','华北','西南'][i%4]
    sales.append([f'SO-{i+1:05}',str(day),region,['专业版','团队版','企业版'][i%3],r.randint(1,12),round(r.uniform(800,8500)*(1+i/2200),2)])
write('sales',['订单编号','订单日期','地区','产品','数量','销售额'],sales)
product=[[str(date(2026,1,1)+timedelta(days=i%90)),['网页端','移动端','桌面端'][i%3],r.randint(100,500),r.randint(10,80)] for i in range(270)]
write('product',['日期','平台','访问人数','转化人数'],product)
hospital=[[f'合成医院{i+1}', ['上海','杭州','南京','合肥'][i%4],['已联系','评估中','已签约'][i%3],round(120+r.random()*2,5),round(30+r.random()*2,5),r.randint(1,20)] for i in range(80)]
write('hospital',['医院','城市','阶段','经度','纬度','拜访次数'],hospital)
wb=openpyxl.Workbook();ws=wb.active;ws.title='说明';ws.append(['合成数据，仅供验收'])
ws=wb.create_sheet('中文销售');ws.append(['合成销售 - 第二行为表头']);ws.append(['日期','地区','销售额'])
from datetime import datetime
ws.append([datetime(2026,1,1),'华东',100]);ws.append([datetime(2026,1,2),'华南',None]);ws.append([datetime(2026,2,3),'华东',300]);ws.append([datetime(2026,2,4),'华南','=100+200'])
wb.save(root/'中文多工作表.xlsx')
(root/'重复表头-gb18030.csv').write_bytes('地区,金额,金额\n华东,100,200\n华南,非法,300\n'.encode('gb18030'))
db=root/'sample.sqlite'
with sqlite3.connect(db) as c:
    c.execute('CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, region TEXT, amount REAL)')
    c.execute('DELETE FROM orders');c.executemany('INSERT INTO orders VALUES(?,?,?)',[(1,'East',100),(2,'West',200),(3,'East',300)])
print('Generated synthetic samples and SQLite fixture')
