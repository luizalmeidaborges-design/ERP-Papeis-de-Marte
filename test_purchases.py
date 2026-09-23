import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from core import Store, export_report_pdf


class PurchaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.temp.name)/'marte.db')
        self.mid=self.store.save_material(name='Ilhos',pack_qty=100,unit='un',pack_cents=1000,
                                         variants=['Azul','Branco'])
        self.vid=self.store.variants(self.mid)[0]['id']

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def item(self,qty=200,paid=3000,variant=None):
        return dict(material_id=self.mid,variant_id=variant or self.vid,qty=qty,total_cents=paid)

    def test_purchase_updates_variant_stock_pack_price_date_and_persists(self):
        pid=self.store.save_purchase(items=[self.item()],supplier='Fornecedor')
        self.assertEqual(self.store.purchases()[0]['total_cents'],3000)
        self.assertEqual(self.store.materials()[0]['pack_cents'],1500)
        self.assertEqual(self.store.materials()[0]['price_date'],date.today().isoformat())
        self.assertEqual(next(r['balance'] for r in self.store.stock() if r['variant_id']==self.vid),200)
        self.assertEqual(self.store.purchase_items(pid)[0]['qty'],200)
        self.store.close();self.store=Store(Path(self.temp.name)/'marte.db')
        self.assertEqual(len(self.store.purchases()),1)
        self.assertEqual(self.store.stock_history(self.mid,variant_id=self.vid)[0]['kind'],'purchase')

    def test_multiple_colors_share_weighted_price(self):
        other=self.store.variants(self.mid)[1]['id']
        self.store.save_purchase(items=[self.item(qty=100,paid=1000),self.item(qty=100,paid=2000,variant=other)])
        self.assertEqual(self.store.materials()[0]['pack_cents'],1500)
        self.assertEqual(self.store.financial_summary()['stock_value'],3000)

    def test_invalid_item_and_write_failure_roll_back_entire_purchase(self):
        invalid=self.item();invalid['variant_id']=999999
        with self.assertRaises(ValueError):self.store.save_purchase(items=[self.item(),invalid])
        self.assertEqual(len(self.store.purchases()),0)
        original=self.store._record_movement
        def fail(*args,**kwargs):
            original(*args,**kwargs)
            raise RuntimeError('Falha simulada')
        with patch.object(self.store,'_record_movement',side_effect=fail):
            with self.assertRaises(RuntimeError):self.store.save_purchase(items=[self.item()])
        self.assertEqual(len(self.store.purchases()),0)
        self.assertEqual(self.store.materials()[0]['pack_cents'],1000)
        self.assertEqual(sum(r['balance'] for r in self.store.stock()),0)

    def test_monthly_result_excludes_gifts_and_inventory_is_current(self):
        self.store.save_purchase(items=[self.item()])
        item=dict(product_id=None,description='Pedido',qty=1,unit_cents=5000)
        self.store.save_order(customer='Cliente',due_date=date.today().isoformat(),payment='Pago',
                              production='Novo',notes='',items=[item])
        self.store.save_order(customer='Presente',due_date=date.today().isoformat(),payment='Presente',
                              production='Novo',notes='',items=[item])
        today=date.today()
        data=self.store.report_data(today.month,today.year)
        self.assertEqual(data['financial']['sales'],5000)
        self.assertEqual(data['financial']['spent'],3000)
        self.assertEqual(data['financial']['balance'],2000)
        old=self.store.report_data(1,2000)['financial']
        self.assertEqual(old['balance'],0)
        self.assertEqual(old['stock_value'],3000)
        export_report_pdf(data,Path(self.temp.name)/'relatorio.pdf')
        self.assertGreater((Path(self.temp.name)/'relatorio.pdf').stat().st_size,1000)

    def test_negative_variant_stock_does_not_reduce_other_stock_value(self):
        other=self.store.variants(self.mid)[1]['id']
        self.store.save_purchase(items=[self.item(qty=100,paid=1000)])
        self.store.adjust_stock(self.mid,'manual_out',50,'Teste',variant_id=other)
        self.assertEqual(self.store.financial_summary()['stock_value'],1000)
