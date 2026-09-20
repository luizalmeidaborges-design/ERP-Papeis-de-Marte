"""Checks for imported data, price calculations and the offline order workflow."""
import tempfile
import unittest
import sqlite3
from datetime import date
from pathlib import Path

from core import Store, asset, automatic_code, cents, export_order_pdf, export_report_pdf, filter_orders, parse_date


@unittest.skipUnless(asset('Precificação.xlsx').is_file(),
                     'Os testes da importação histórica exigem a planilha local privada.')
class ERPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'marte.db'
        self.store=Store(self.path,asset('Precificação.xlsx'))
        self.addCleanup(self.store.close)

    def test_import_preserves_history_and_flags_missing_costs(self):
        self.assertEqual((len(self.store.materials()),len(self.store.products()),len(self.store.orders())),(42,11,8))
        self.assertEqual(self.store.dashboard()['revenue'],50500)
        self.assertEqual(self.store.next_number(),'PM0009')
        pre=self.store.one("SELECT id FROM products WHERE code='PRE001'")
        kit=self.store.one("SELECT id FROM products WHERE code='KIT001'")
        self.assertEqual(self.store.product_cost(pre['id'])[1],['FITCET'])
        self.assertIsNone(self.store.product_cost(kit['id'])[0])
        unknown=self.store.one("SELECT id FROM orders WHERE number='PM0007'")
        self.assertIsNone(self.store.items(unknown['id'])[0]['unit_cents'])

    def test_price_recalculates_and_recipe_tracks_renamed_material(self):
        product=self.store.one("SELECT * FROM products WHERE code='PAP001'")
        before=self.store.product_cost(product['id'])[0]
        self.assertAlmostEqual(before,321)
        m=self.store.one("SELECT * FROM materials WHERE code='BOPA4'")
        self.store.save_material(id=m['id'],code='BOPPNOVO',name=m['name'],
          specification=m['specification'],pack_qty=m['pack_qty'],unit=m['unit'],pack_cents=8400)
        after=self.store.product_cost(product['id'])[0]
        self.assertAlmostEqual(after,before+126)
        self.assertEqual(self.store.product_cost(product['id'])[1],[])

    def test_generated_codes_and_separate_attributes(self):
        self.assertEqual(automatic_code('Offset','A4','150'),'OFFA4150')
        self.assertEqual(automatic_code('Ácido','A5','120'),'ACIA5120')
        self.store.save_material(name='Cartolina',size='A3',grammage='180',pack_qty=10,
                                 unit='un',pack_cents=1000)
        material=self.store.one("SELECT * FROM materials WHERE code='CARA3180'")
        self.assertEqual((material['size'],material['grammage']),('A3','180'))
        product_id=self.store.save_product(name='Cartão',size='A3',grammage='180',markup=1.8,
                                           table_cents=None,recipe=[('CARA3180',2)])
        product=self.store.one('SELECT * FROM products WHERE id=?',(product_id,))
        self.assertEqual((product['code'],product['size'],product['grammage']),('CARA3180','A3','180'))

    def test_existing_database_is_migrated_without_losing_codes(self):
        old_path=Path(self.tmp.name)/'legacy.db'
        with sqlite3.connect(old_path) as legacy:
            legacy.execute('CREATE TABLE materials(id INTEGER PRIMARY KEY,code TEXT,name TEXT,specification TEXT,pack_qty REAL,unit TEXT,pack_cents INTEGER,active INTEGER)')
            legacy.execute('CREATE TABLE products(id INTEGER PRIMARY KEY,code TEXT,name TEXT,markup REAL,table_cents INTEGER,active INTEGER)')
            legacy.execute('''CREATE TABLE stock_movements(id INTEGER PRIMARY KEY,material_id INTEGER,
                order_id INTEGER,delta REAL,kind TEXT,notes TEXT,effective_date TEXT,created_at TEXT)''')
            legacy.execute("INSERT INTO materials VALUES(1,'OFFA4150','Offset','A4 · 150',125,'un',3300,1)")
            legacy.execute("INSERT INTO products VALUES(1,'CAD001','Caderno',1.8,3000,1)")
            legacy.execute("INSERT INTO stock_movements VALUES(1,1,NULL,8,'entry','Saldo anterior','2026-09-19','2026-09-19T12:00:00')")
        migrated=Store(old_path,asset('Precificação.xlsx'))
        try:
            m=migrated.one('SELECT * FROM materials WHERE id=1')
            p=migrated.one('SELECT * FROM products WHERE id=1')
            self.assertEqual((m['code'],m['size'],m['grammage']),('OFFA4150','A4','150'))
            self.assertEqual((p['code'],p['size']),( 'CAD001',''))
            self.assertEqual(len(migrated.products()),1)
            migrated.save_material(id=1,code=m['code'],name=m['name'],size=m['size'],
                grammage=m['grammage'],specification='',pack_qty=m['pack_qty'],unit=m['unit'],
                pack_cents=m['pack_cents'],variants=['Branco','Preto'])
            balances={r['variant_name']:r['balance'] for r in migrated.stock()}
            self.assertEqual(balances['Sem variação (legado)'],8)
            self.assertEqual(balances['Branco'],0)
            white=migrated.variants(1,active_only=True)[0]['id']
            migrated.adjust_stock(1,'entry',4,'Nova cor',variant_id=white)
            self.assertEqual(migrated.stock_history(1,variant_id=white)[0]['delta'],4)
            self.assertEqual(migrated.stock_history(1)[0]['delta'],8)
            migrated.transfer_stock(1,None,white,3,'Distribuição do saldo antigo')
            self.assertEqual(next(r['balance'] for r in migrated.stock() if r['variant_id']==white),7)
            self.assertEqual(next(r['balance'] for r in migrated.stock() if r['variant_name']=='Sem variação (legado)'),5)
            with self.assertRaisesRegex(ValueError,'saldo suficiente'):
                migrated.transfer_stock(1,None,white,6,'Quantidade excessiva')
        finally:migrated.close()

    def test_order_average_snapshot_pdf_and_restart(self):
        product=self.store.one("SELECT * FROM products WHERE code='PAP001'")
        due=parse_date('28/09/2026')
        id=self.store.save_order(customer='Cliente de teste',due_date=due,
            payment='Pendente',production='Novo',notes='Arte personalizada',
            items=[dict(product_id=product['id'],description=product['name'],qty=2,unit_cents=cents('12,50')),
                   dict(product_id=None,description='Embalagem especial',qty=1,unit_cents=cents('5,00'))])
        order=self.store.order(id)
        self.assertEqual(order['number'],'PM0009')
        self.assertEqual(order['due_date'],'2026-09-28')
        self.assertEqual(self.store.mean_price(product['id']),1250)
        total=next(row for row in self.store.orders() if row['id']==id)
        self.assertEqual(total['total_cents'],3000)
        pdf=Path(self.tmp.name)/'pedido.pdf'
        export_order_pdf(self.store,id,pdf)
        from pypdf import PdfReader
        text=' '.join(page.extract_text() for page in PdfReader(pdf).pages)
        self.assertIn('PM0009',text)
        self.assertIn('28/09/2026',text)
        self.assertIn('30,00',text)
        self.store.backup(Path(self.tmp.name)/'copia.db')
        other=Store(Path(self.tmp.name)/'copia.db',asset('Precificação.xlsx'))
        try:
            self.assertEqual(len(other.orders()),9)
        finally:
            other.close()

    def test_column_filters_and_period_report_pdf(self):
        id=self.store.save_order(customer='Cliente filtro',due_date='2026-09-28',payment='Pago',
            production='Entregue',notes='',items=[dict(product_id=None,description='Caderno especial',
                                                      qty=2,unit_cents=1500)])
        orders=self.store.orders()
        self.assertEqual([o['id'] for o in filter_orders(orders,{'customer':'filtro','payment':'Pago'})],[id])
        self.assertEqual([o['id'] for o in filter_orders(orders,{'due':'28/09','min_total':3000})],[id])
        self.assertEqual(filter_orders(orders,{'max_total':1000,'customer':'filtro'}),[])
        today=date.today()
        data=self.store.report_data(today.month,today.year)
        self.assertEqual((data['count'],data['open'],data['revenue'],data['average_ticket']),
                         (1,0,3000,3000))
        self.assertEqual(self.store.report_data()['count'],9)
        self.assertEqual(self.store.report_data()['unknown'],1)
        with self.assertRaises(ValueError):self.store.report_data(13,2026)
        pdf=Path(self.tmp.name)/'relatorio.pdf'
        export_report_pdf(data,pdf)
        from pypdf import PdfReader
        contents=' '.join(page.extract_text() for page in PdfReader(pdf).pages)
        self.assertIn('Cliente filtro',contents)
        self.assertIn('Caderno especial',contents)
        self.assertIn('30,00',contents)

    def test_inventory_deducts_orders_once_and_records_manual_changes(self):
        product=self.store.one("SELECT * FROM products WHERE code='PAP001'")
        recipe=self.store.recipe(product['id'])
        for part in recipe:
            m=self.store.one('SELECT * FROM materials WHERE code=? COLLATE NOCASE',(part['material_code'],))
            self.store.adjust_stock(m['id'],'entry',20,'Saldo inicial contado')
        items=[dict(product_id=product['id'],description=product['name'],qty=2,unit_cents=1200)]
        id=self.store.save_order(customer='Cliente estoque',due_date='2026-10-10',
            payment='Pendente',production='Novo',notes='',items=items)
        material=self.store.one('SELECT id FROM materials WHERE code=? COLLATE NOCASE',(recipe[0]['material_code'],))
        def balance():
            return next(r['balance'] for r in self.store.stock() if r['id']==material['id'])
        used=2*recipe[0]['qty']
        self.assertEqual(balance(),20-used)
        movements=len(self.store.stock_history(material['id']))
        self.store.save_order(id=id,customer='Cliente estoque',due_date='2026-10-11',
            payment='Pago',production='Entregue',notes='Somente status',items=items)
        self.assertEqual(balance(),20-used)
        self.assertEqual(len(self.store.stock_history(material['id'])),movements)
        changed=[dict(items[0],qty=3)]
        self.store.save_order(id=id,customer='Cliente estoque',due_date='2026-10-11',
            payment='Pago',production='Entregue',notes='',items=changed)
        self.assertEqual(balance(),20-3*recipe[0]['qty'])
        history=self.store.stock_history(material['id'])
        self.assertEqual(history[0]['kind'],'order_out')
        self.assertEqual(history[1]['kind'],'order_reversal')
        self.assertEqual(history[0]['effective_date'],date.today().isoformat())
        self.store.adjust_stock(material['id'],'manual_out',30,'Retirada forçada')
        self.assertLess(balance(),0)
        self.store.adjust_stock(material['id'],'adjustment',0,'Contagem física')
        self.assertAlmostEqual(balance(),0)
        with self.assertRaises(ValueError):self.store.adjust_stock(material['id'],'entry',2,'')

    def test_incomplete_recipe_cannot_create_partial_inventory_movement(self):
        product=self.store.one("SELECT * FROM products WHERE code='PRE001'")
        before=len(self.store.orders())
        with self.assertRaisesRegex(ValueError,'composição'):
            self.store.save_order(customer='Cliente',due_date='2026-10-10',payment='Pendente',
                production='Novo',notes='',items=[dict(product_id=product['id'],description='Closet',
                                                     qty=1,unit_cents=3490)])
        self.assertEqual(len(self.store.orders()),before)
        self.assertFalse(self.store.all('SELECT 1 FROM stock_movements LIMIT 1'))

    def test_deleting_order_restores_inventory_and_does_not_reuse_number(self):
        product=self.store.one("SELECT * FROM products WHERE code='PAP001'")
        part=self.store.recipe(product['id'])[0]
        material=self.store.one('SELECT id FROM materials WHERE code=? COLLATE NOCASE',
                                (part['material_code'],))
        item=dict(product_id=product['id'],description=product['name'],qty=2,unit_cents=1200)
        oid=self.store.save_order(customer='Pedido removido',due_date='2026-10-10',
            payment='Pendente',production='Novo',notes='',items=[item])
        self.assertEqual(self.store.order(oid)['number'],'PM0009')
        def saldo():
            return next(row['balance'] for row in self.store.stock() if row['id']==material['id'])
        self.assertAlmostEqual(saldo(),-2*part['qty'])
        self.store.delete_order(oid)
        self.assertIsNone(self.store.order(oid))
        self.assertEqual(len(self.store.orders()),8)
        self.assertAlmostEqual(saldo(),0)
        movements=self.store.stock_history(material['id'])
        self.assertEqual(movements[0]['kind'],'order_reversal')
        self.assertTrue(all(row['order_id'] is None for row in movements))
        self.assertEqual(self.store.next_number(),'PM0010')
        with self.assertRaisesRegex(ValueError,'não encontrado'):
            self.store.delete_order(oid)
        new_id=self.store.save_order(customer='Próximo pedido',due_date='2026-10-12',
            payment='Pendente',production='Novo',notes='',items=[item])
        self.assertEqual(self.store.order(new_id)['number'],'PM0010')

    def test_color_variants_share_cost_and_split_order_stock(self):
        wire=self.store.one("SELECT * FROM materials WHERE code='WIR120'")
        eyelet=self.store.one("SELECT * FROM materials WHERE code='ILH'")
        product=self.store.one("SELECT * FROM products WHERE code='CAD001'")
        old_cost=self.store.product_cost(product['id'])[0]
        for m,names in ((wire,['Branco','Dourado']),(eyelet,['Prata','Dourado'])):
            self.store.save_material(id=m['id'],code=m['code'],name=m['name'],size=m['size'],
                grammage=m['grammage'],specification=m['specification'],pack_qty=m['pack_qty'],
                unit=m['unit'],pack_cents=m['pack_cents'],variants=names)
        self.assertEqual(old_cost,self.store.product_cost(product['id'])[0])
        def variant(material_id,name):
            return next(v['id'] for v in self.store.variants(material_id,active_only=True) if v['name']==name)
        wb=variant(wire['id'],'Branco');wd=variant(wire['id'],'Dourado')
        ep=variant(eyelet['id'],'Prata');ed=variant(eyelet['id'],'Dourado')
        item=dict(product_id=product['id'],description=product['name'],qty=2,unit_cents=3000,
                  variants={wire['id']:wd,eyelet['id']:ep})
        with self.assertRaisesRegex(ValueError,'variação'):
            self.store.save_order(customer='Teste',due_date='2026-10-10',payment='Pago',
                production='Novo',notes='',items=[dict(item,variants={wire['id']:wd})])
        self.assertEqual(len(self.store.orders()),8)
        oid=self.store.save_order(customer='Teste',due_date='2026-10-10',payment='Pago',
            production='Novo',notes='',items=[item])
        def saldo(mid,vid):
            return next(r['balance'] for r in self.store.stock() if r['id']==mid and r['variant_id']==vid)
        self.assertEqual(saldo(wire['id'],wd),-32)
        self.assertEqual(saldo(wire['id'],wb),0)
        self.assertEqual(saldo(eyelet['id'],ep),-4)
        self.assertEqual(saldo(eyelet['id'],ed),0)
        self.assertIn('Dourado',next(o for o in self.store.orders() if o['id']==oid)['descriptions'])
        pdf=Path(self.tmp.name)/'cores.pdf'
        export_order_pdf(self.store,oid,pdf)
        from pypdf import PdfReader
        content=' '.join(page.extract_text() for page in PdfReader(pdf).pages)
        self.assertIn('Wire-o: Dourado',content)
        self.assertIn('Ilhós: Prata',content)
        self.store.save_order(id=oid,customer='Teste',due_date='2026-10-10',payment='Pendente',
            production='Novo',notes='Mudança apenas de status',items=[item])
        self.assertEqual(len(self.store.stock_history(wire['id'],variant_id=wd)),1)
        new_item=dict(item,variants={wire['id']:wb,eyelet['id']:ed})
        self.store.save_order(id=oid,customer='Teste',due_date='2026-10-10',payment='Pendente',
            production='Novo',notes='',items=[new_item])
        self.assertEqual(saldo(wire['id'],wd),0)
        self.assertEqual(saldo(wire['id'],wb),-32)
        self.assertEqual(saldo(eyelet['id'],ep),0)
        self.assertEqual(saldo(eyelet['id'],ed),-4)
        self.store.save_material(id=wire['id'],code=wire['code'],name=wire['name'],size=wire['size'],
            grammage=wire['grammage'],specification=wire['specification'],pack_qty=wire['pack_qty'],
            unit=wire['unit'],pack_cents=wire['pack_cents'],variants=['Dourado'])
        self.assertEqual(saldo(wire['id'],wb),-32)
        self.assertFalse(next(v for v in self.store.variants(wire['id']) if v['id']==wb)['active'])
        reopened=Store(self.path,asset('Precificação.xlsx'))
        try:
            self.assertEqual(reopened.items(oid)[0]['variants'][wire['id']],wb)
            self.assertEqual(next(r['balance'] for r in reopened.stock()
                                  if r['id']==wire['id'] and r['variant_id']==wb),-32)
        finally:reopened.close()
        self.store.delete_order(oid)
        self.assertEqual(saldo(wire['id'],wb),0)
        self.assertEqual(saldo(eyelet['id'],ed),0)


if __name__=='__main__':
    unittest.main()
