"""Compras recebidas e pagas, com entrada e preço atualizados atomicamente."""
import math
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class Purchasing:
    def init_purchases(self):
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY, purchase_date TEXT NOT NULL,
            supplier TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
            total_cents INTEGER NOT NULL CHECK(total_cents>=0)
          );
          CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY, purchase_id INTEGER NOT NULL REFERENCES purchases(id),
            material_id INTEGER NOT NULL REFERENCES materials(id),
            variant_id INTEGER REFERENCES material_variants(id),
            description TEXT NOT NULL, unit TEXT NOT NULL,
            qty REAL NOT NULL CHECK(qty>0), total_cents INTEGER NOT NULL CHECK(total_cents>=0)
          );
        ''')

    def purchases(self):
        return self.all('SELECT * FROM purchases ORDER BY purchase_date DESC,id DESC')

    def purchase_items(self, purchase_id):
        return self.all('SELECT * FROM purchase_items WHERE purchase_id=? ORDER BY id',(purchase_id,))

    def save_purchase(self, *, items, supplier='', notes=''):
        if not items:raise ValueError('Adicione ao menos um insumo à compra.')
        validated=[]
        for item in items:
            material=self.one('SELECT * FROM materials WHERE id=? AND active=1',(item['material_id'],))
            if material is None:raise ValueError('Insumo inválido ou inativo.')
            qty=item['qty'];paid=item['total_cents'];variant=item.get('variant_id')
            if not math.isfinite(qty) or qty<=0 or qty>1000000:
                raise ValueError('Quantidade da compra inválida.')
            if not isinstance(paid,int) or isinstance(paid,bool) or paid<0:
                raise ValueError('Informe o total pago pelo item, em reais.')
            label=f"{material['code']} · {material['name']}"
            if variant is not None:
                option=self.one('SELECT name FROM material_variants WHERE id=? AND material_id=? AND active=1',
                                (variant,material['id']))
                if option is None:raise ValueError('Variação inválida ou inativa.')
                label+=' · '+option['name']
            elif self.variants(material['id']):
                raise ValueError('Escolha a variação do insumo.')
            validated.append((material,variant,qty,paid,label))
        today=date.today().isoformat()
        with self.db:
            pid=self.db.execute('INSERT INTO purchases(purchase_date,supplier,notes,total_cents) VALUES(?,?,?,?)',
                (today,supplier.strip(),notes.strip(),sum(row[3] for row in validated))).lastrowid
            totals=defaultdict(lambda:[Decimal(0),0,None])
            for material,variant,qty,paid,label in validated:
                self.db.execute('''INSERT INTO purchase_items(purchase_id,material_id,variant_id,description,unit,qty,total_cents)
                    VALUES(?,?,?,?,?,?,?)''',(pid,material['id'],variant,label,material['unit'],qty,paid))
                self._record_movement(material['id'],qty,'purchase',f'Compra OC{pid:05d}',variant_id=variant)
                totals[material['id']][0]+=Decimal(str(qty))
                totals[material['id']][1]+=paid
                totals[material['id']][2]=material
            for mid,(qty,paid,material) in totals.items():
                pack_price=int((Decimal(paid)*Decimal(str(material['pack_qty']))/qty).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                self.db.execute('UPDATE materials SET pack_cents=?,price_date=? WHERE id=?',(pack_price,today,mid))
        return pid

    def financial_summary(self, month=None, year=None):
        # Vendas por cadastro; não equivale a recebimentos por data de pagamento.
        monthly=defaultdict(lambda:{'sales':0,'spent':0})
        for order in self.orders():
            key=(order['created_date'] or '')[:7] or 'Sem data'
            if not order['unpriced'] and order['payment']!='Presente':
                monthly[key]['sales']+=round(order['total_cents'] or 0)
        for purchase in self.purchases():
            monthly[purchase['purchase_date'][:7]]['spent']+=purchase['total_cents']
        if month:
            keys=[f'{year:04d}-{month:02d}']
        else:
            keys=sorted(monthly,reverse=True)
        rows=[dict(period=key,**monthly[key],balance=monthly[key]['sales']-monthly[key]['spent']) for key in keys]
        stock_value=round(sum(max(0,row['balance'])*row['pack_cents']/row['pack_qty'] for row in self.stock()))
        return {'rows':rows,'sales':sum(r['sales'] for r in rows),'spent':sum(r['spent'] for r in rows),
                'balance':sum(r['balance'] for r in rows),'stock_value':stock_value}
