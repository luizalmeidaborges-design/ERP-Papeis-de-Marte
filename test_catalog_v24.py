import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from core import Store
from catalog_core import positive_int


class Catalog24Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'db.sqlite';self.s=Store(self.path)
        self.mid=self.s.save_material(name='Offset',code='OFF',pack_qty=1,unit='folha A4',pack_cents=600)
        self.s.adjust_stock(self.mid,'entry',100,'Inicial')
        self.pid=self.s.save_product(name='Marca página',code='MAR',markup=2,base_yield=6,table_cents=None,kits='1,6,12',recipe=[('OFF',1)])

    def tearDown(self):self.s.close();self.temp.cleanup()

    def stock(self):return next(r['balance'] for r in self.s.stock() if r['id']==self.mid)
    def ready(self):return next(r['balance'] for r in self.s.product_stock() if r['id']==self.pid)
    def order(self,n,source='production',id=None,items=None):
        items=items or [dict(product_id=self.pid,description='Marca página',qty=n,variants={},**self.s.order_quote(self.pid,n,source))]
        return self.s.save_order(id=id,customer='Cliente',due_date='2026-10-10',payment='Pendente',production='Novo',notes='',items=items)

    def test_minimum_batch_and_seventh_piece(self):
        for n,batches,cost,sale in [(1,1,600,1200),(6,1,600,1200),(7,2,1200,2401),(12,2,1200,2400)]:
            with self.subTest(qty=n):
                q=self.s.order_quote(self.pid,n)
                self.assertEqual(q['batches'],batches)
                self.assertAlmostEqual(q['cost_unit_cents']*n,cost)
                self.assertEqual(q['unit_cents']*n,sale)
        for n in (0,-1,1.2,'1.5',True):
            with self.assertRaises(ValueError):self.s.order_quote(self.pid,n)
        self.assertEqual(positive_int(6.0),6)

    def test_stock_ready_no_second_material_consumption_and_reversal(self):
        first=self.order(1)
        self.assertEqual(self.stock(),99);self.assertEqual(self.ready(),5)
        second=self.order(3,'stock')
        self.assertEqual(self.stock(),99);self.assertEqual(self.ready(),2)
        with self.assertRaises(ValueError):self.s.delete_order(first)
        self.assertIsNotNone(self.s.order(first));self.assertEqual(self.stock(),99)
        self.s.delete_order(second);self.assertEqual(self.ready(),5)
        self.s.delete_order(first);self.assertEqual(self.ready(),0);self.assertEqual(self.stock(),100)

    def test_finished_stock_shortage_rolls_back_entire_order(self):
        with self.assertRaises(ValueError):self.order(1,'stock')
        self.assertFalse(self.s.orders());self.assertEqual(self.stock(),100);self.assertEqual(self.ready(),0)

    def test_edit_qty_reverses_batches_without_double_deduction(self):
        oid=self.order(1);self.order(7,id=oid)
        self.assertEqual(self.stock(),98);self.assertEqual(self.ready(),5)
        self.order(6,id=oid);self.assertEqual(self.stock(),99);self.assertEqual(self.ready(),0)
        self.s.delete_order(oid);self.assertEqual(self.stock(),100)

    def test_edit_other_item_keeps_original_recipe_snapshot(self):
        oid=self.order(1);saved=self.s.items(oid)[0]
        self.s.save_product(id=self.pid,name='Marca página',code='MAR',markup=2,base_yield=12,table_cents=None,recipe=[('OFF',3)])
        new=dict(product_id=None,description='Avulso',qty=1,unit_cents=100,variants={})
        self.order(1,id=oid,items=[saved,new])
        self.assertEqual(self.stock(),99);self.assertEqual(self.ready(),5)
        self.assertEqual(self.s.items(oid)[0]['cost_unit_cents'],600)

    def test_legacy_order_keeps_proportional_consumption(self):
        item=dict(product_id=self.pid,description='Antigo',qty=1,unit_cents=200,pricing_mode='legacy',variants={})
        oid=self.order(1,items=[item]);self.assertAlmostEqual(self.stock(),100-1/6)
        self.s.close();self.s=Store(self.path)
        items=self.s.items(oid)
        self.order(1,id=oid,items=items);self.assertAlmostEqual(self.stock(),100-1/6)
        self.assertEqual(self.ready(),0)

    def test_many_options_prices_and_generated_products(self):
        opts=[dict(option=f'Wire-o {i}',value='Dourado',pack_cents=100+i*10) for i in range(8)]
        mid=self.s.save_material(name='Wire-o',code='WIR',pack_qty=1,unit='un',pack_cents=99,variant_options=opts,category='Produção')
        pid=self.s.save_product(name='Caderno',code='CAD',markup=2,table_cents=None,recipe=[('WIR',1)])
        self.assertEqual(self.s.product_cost(pid)[0],170)
        children=self.s.generate_cost_variations(pid)
        self.assertEqual(len(children),8);self.assertEqual(self.s.generate_cost_variations(pid),[])
        costs=sorted(self.s.product_cost(i)[0] for i in children);self.assertEqual(costs,list(range(100,180,10)))
        self.assertEqual(len(self.s.variants(mid,True)),8)
        for child in children:
            self.assertEqual(self.s.variant_requirements(child),[])
            self.assertEqual(self.s.one('SELECT cost_unit_cents FROM products WHERE id=?',(child,))['cost_unit_cents'],self.s.product_cost(child)[0])

    def test_renaming_option_preserves_stock_id_and_history(self):
        mid=self.s.save_material(name='Ilhós',code='ILH',pack_qty=100,unit='un',pack_cents=1000,variants=['Prata'])
        vid=self.s.variants(mid)[0]['id'];self.s.adjust_stock(mid,'entry',20,'Inicial',variant_id=vid)
        self.s.save_material(id=mid,name='Ilhós',code='ILH',pack_qty=100,unit='un',pack_cents=1000,
            variant_options=[dict(id=vid,option='Ilhós 5mm',value='Prata',pack_cents=None)])
        self.assertEqual(self.s.variants(mid,True)[0]['id'],vid)
        self.assertEqual(next(r['balance'] for r in self.s.stock() if r['variant_id']==vid),20)

    def test_fixed_default_cost_not_max_and_live_cache_updates(self):
        mid=self.s.save_material(name='BOPP',code='BOP',pack_qty=1,unit='folha',pack_cents=100,
            variant_options=[dict(option='Tipo',value='Brilhante',pack_cents=None),dict(option='Tipo',value='Holográfico',pack_cents=300)])
        vid=next(v['id'] for v in self.s.variants(mid) if v['value_name']=='Brilhante')
        pid=self.s.save_product(name='Brilhante',code='BRI',markup=2,table_cents=None,recipe=[('BOP',1)],choices={mid:vid})
        self.assertEqual(self.s.product_cost(pid)[0],100)
        self.assertEqual(self.s.one('SELECT cost_total_cents FROM products WHERE id=?',(pid,))['cost_total_cents'],100)
        self.s.db.execute('UPDATE materials SET pack_cents=200 WHERE id=?',(mid,));self.s.db.commit()
        self.assertEqual(self.s.one('SELECT cost_total_cents FROM products WHERE id=?',(pid,))['cost_total_cents'],200)

    def test_bopp_version_has_independent_recipe_and_stock(self):
        self.s.save_material(name='Holográfico',code='HOL',pack_qty=1,unit='folha',pack_cents=900,category='Produção')
        child=self.s.create_product_variation(self.pid,name='Marca Holo',code='MARHOL',label='Holográfico',recipe=[('HOL',1)])
        self.assertEqual(self.s.recipe(self.pid)[0]['material_code'],'OFF')
        self.assertEqual(self.s.product_cost(child)[0],150)
        self.s.adjust_product_stock(child,'entry',4,'Inicial')
        self.assertEqual(self.ready(),0)

    def test_customer_validation_and_persistence(self):
        cid=self.s.save_customer(name='Thayna',phone='11999999999',email='t@example.com',birthday='1995-05-03',address='Rua A, 10')
        oid=self.s.save_order(customer='',customer_id=cid,due_date='2026-10-10',payment='Pago',production='Novo',notes='',items=[dict(product_id=None,description='Avulso',qty=1,unit_cents=100)])
        self.assertEqual(self.s.order(oid)['customer'],'Thayna')
        self.s.close();self.s=Store(self.path);self.assertEqual(self.s.order(oid)['customer_id'],cid)
        for data in [dict(name=''),dict(name='X',email='abc'),dict(name='X',birthday='2999-01-01')]:
            with self.assertRaises(ValueError):self.s.save_customer(**data)

    def csvrow(self,code='NEW',name='Novo'):
        return dict(line=2,data=dict(nome=name,codigo=code,tamanho='A4',gramatura='180',rendimento='6',multiplicador='1,8',kits='1|6|12',preco_unitario='',insumos='OFF=1',variacoes=''))

    def test_csv_valid_invalid_correction_and_duplicate_only_invalid_skipped(self):
        a=self.csvrow();b=self.csvrow('BAD','Ruim');b['data']['insumos']='MISSING=1'
        added,errors=self.s.import_csv_products([a,b,self.csvrow()])
        self.assertEqual(len(added),1);self.assertEqual(len(errors),2)
        errors[0]['data']['insumos']='OFF=1';added,errors=self.s.import_csv_products(errors[:1])
        self.assertEqual(len(added),1);self.assertFalse(errors)

    def test_csv_delimiter_bom_and_template_header(self):
        self.assertEqual(len(self.s.parse_product_csv('\ufeff'+self.s.csv_template())),1)
        out=io.StringIO();w=csv.DictWriter(out,fieldnames=self.s.CSV_FIELDS);w.writeheader();w.writerow(self.csvrow()['data'])
        self.assertEqual(self.s.parse_product_csv(out.getvalue())[0]['data']['multiplicador'],'1,8')
        for text in ('','nome;codigo\nA;B'):
            with self.assertRaises(ValueError):self.s.parse_product_csv(text)

    def test_invalid_product_atomic_and_kits_validation(self):
        for kits in ('0','1,0','1,2.5',''):
            with self.assertRaises(ValueError):self.s.save_product(name='X',code='X',markup=2,table_cents=None,recipe=[('OFF',1)],kits=kits)
        with self.assertRaises(ValueError):self.s.save_product(name='X',code='X',markup=2,table_cents=None,recipe=[('OFF',1),('MISSING',1)])
        self.assertIsNone(self.s.one("SELECT * FROM products WHERE code='X'"))

    def test_category_and_product_stock_value_persist(self):
        self.s.save_material(name='Saco',code='SAC',pack_qty=100,unit='un',pack_cents=500,category='Embalagem')
        self.s.adjust_product_stock(self.pid,'entry',12,'Inicial')
        summary=self.s.financial_summary()
        self.assertEqual(summary['product_stock_value'],1200)
        self.assertEqual(summary['stock_value'],summary['product_stock_value']+summary['material_stock_value'])
        self.s.close();self.s=Store(self.path)
        self.assertEqual(self.s.one("SELECT category FROM materials WHERE code='SAC'")['category'],'Embalagem')
        self.assertEqual(self.ready(),12)

    def test_purchase_updates_only_priced_variant(self):
        mid=self.s.save_material(name='BOPP',code='BOP',pack_qty=10,unit='folha',pack_cents=100,
            variant_options=[dict(option='Tipo',value='Fosco',pack_cents=200),dict(option='Tipo',value='Holo',pack_cents=400)])
        options=self.s.variants(mid,True);vid=next(v['id'] for v in options if v['value_name']=='Fosco')
        other=next(v['id'] for v in options if v['value_name']=='Holo')
        self.s.save_purchase(items=[dict(material_id=mid,variant_id=vid,qty=10,total_cents=300)])
        self.assertEqual(self.s.material_price(mid,vid),300)
        self.assertEqual(self.s.material_price(mid,other),400)
        self.assertEqual(self.s.one('SELECT pack_cents FROM materials WHERE id=?',(mid,))['pack_cents'],100)

    def test_removing_production_line_cannot_erase_consumed_surplus(self):
        first=self.order(1);self.order(3,'stock')
        with self.assertRaises(ValueError):
            self.order(1,id=first,items=[dict(product_id=None,description='Avulso',qty=1,unit_cents=100)])
        self.assertEqual(self.ready(),2);self.assertEqual(self.stock(),99)
        self.assertEqual(self.s.items(first)[0]['product_id'],self.pid)

if __name__=='__main__':unittest.main()
