import gc
import tempfile
import tkinter as tk
import unittest
import weakref
from pathlib import Path
from unittest.mock import patch
from core import Store
from test_build_510 import Widget


class SettingsDeletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'marte.db'
        self.store=Store(self.path)
    def tearDown(self):self.store.close();self.tmp.cleanup()

    def test_setting_validation_persistence_and_no_reset(self):
        self.assertEqual(self.store.cost_multiplier(),1.8)
        self.store.save_customer(name='Preservar')
        self.store.set_cost_multiplier(' 2,5 ')
        for value in ('','abc','nan','inf','0','0,9','1001'):
            with self.assertRaises(ValueError):self.store.set_cost_multiplier(value)
        self.store.close();self.store=Store(self.path)
        self.assertEqual(self.store.cost_multiplier(),2.5)
        self.assertEqual(self.store.customers()[0]['name'],'Preservar')

    def test_delete_unused_and_block_recipe_and_history(self):
        mid=self.store.save_material(name='Papel',code='PAP',unit='un',pack_qty=1,pack_cents=100,variants=['Azul'])
        self.store.delete_material(mid)
        self.assertEqual(self.store.materials(),[])
        self.assertEqual(self.store.all('SELECT * FROM material_variants'),[])
        mid=self.store.save_material(name='Papel',code='PAP',unit='un',pack_qty=1,pack_cents=100)
        self.store.save_product(name='Produto',code='PRO',markup=2,table_cents=200,recipe=[('PAP',1)])
        with self.assertRaises(ValueError):self.store.delete_material(mid)
        mid2=self.store.save_material(name='Saco',code='SAC',unit='un',pack_qty=1,pack_cents=10)
        self.store.adjust_stock(mid2,'entry',1,'Teste')
        self.store.adjust_stock(mid2,'manual_out',1,'Saldo zero')
        with self.assertRaises(ValueError):self.store.delete_material(mid2)
        self.assertEqual(len(self.store.materials()),2)

    def test_field_keeps_tcl_variable_after_builder_returns(self):
        from app import field
        interpreter=tk.Tcl()
        with patch('app.tk.Frame',Widget),patch('app.tk.Label',Widget),patch('app.ttk.Entry',Widget):
            def build():
                var=tk.StringVar(master=interpreter)
                entry=field(None,'Teste',0,'1,8',variable=var)
                return entry,weakref.ref(var),str(var)
            entry,reference,name=build()
        # Fake widget must not retain the variable through constructor options.
        entry.options.clear();gc.collect()
        self.assertIsNotNone(reference())
        self.assertEqual(interpreter.getvar(name),'1,8')

    def test_stock_filters_refresh_rows_and_clear_old_history(self):
        import app
        from contextlib import ExitStack
        from test_build_510 import Variable
        mid=self.store.save_material(name='Fita',code='FIT',unit='cm',size='7mm',pack_qty=1,pack_cents=10,variants=['Azul','Rosa'])
        variants=self.store.variants(mid)
        self.store.adjust_stock(mid,'entry',10,'Inicial',variant_id=variants[0]['id'])
        ui=app.ERP.__new__(app.ERP);ui.store=self.store;ui.main=Widget()
        ui.toolbar=lambda *a:None;ui.show_stock_history=lambda:None
        with ExitStack() as stack:
            for target,replacement in [('tk.Frame',Widget),('tk.Label',Widget),('tk.StringVar',Variable),
                    ('ttk.Entry',Widget),('ttk.Combobox',Widget),('ttk.Scrollbar',Widget),
                    ('StripedTreeview',Widget),('grid',lambda *a:Widget()),('button',lambda *a:Widget())]:
                stack.enter_context(patch('app.'+target,replacement))
            ui.stock_page()
            self.assertEqual(len(ui.stock_rows),2)
            ui.stock_filter_vars['status'].set('Disponível')
            self.assertEqual(len(ui.stock_rows),1)
            ui.stock_filter_vars['variant'].set('Rosa')
            self.assertEqual(len(ui.stock_rows),0)
            ui.stock_filter_vars['status'].set('')
            self.assertEqual(len(ui.stock_rows),1)
            ui.stock_history_tree.insert('',iid='old',values=('old',))
            ui.stock_filter_vars['text'].set('inexistente')
            self.assertEqual(ui.stock_tree.get_children(),())
            self.assertEqual(ui.stock_history_tree.get_children(),())

if __name__=='__main__':unittest.main()
