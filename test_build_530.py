"""Nested composition, historical stock reversals and quantity editing."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import Store
from test_build_510 import ProductFormTests


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db.sqlite'
        self.s=Store(self.path)
        self.paper=self.s.save_material(name='Papel',code='PAP',pack_qty=1,pack_cents=100,unit='folha',variants=['Azul','Rosa'])
        self.blue=self.s.variants(self.paper)[0]['id']
        self.bag=self.s.save_material(name='Saco',code='SAC',pack_qty=1,pack_cents=20,unit='un')
        self.child=self.product('Z10',[('PAP',2),('SAC',3)],base_yield=2)
        self.parent=self.product('B20',[('PAP',4)],components=[(self.child,3,'Produção')])
        self.top=self.product('A01',[],components=[(self.parent,2,'Produção'),(self.child,1,'Embalagem')])

    def tearDown(self):self.s.close();self.tmp.cleanup()
    def product(self,code,recipe,**kwargs):
        return self.s.save_product(code=code,name='Produto '+code,markup=2,table_cents=9999,recipe=recipe,**kwargs)
    def order(self,qty=2,id=None,payment='Pendente'):
        return self.s.save_order(id=id,customer='Cliente',due_date='2026-10-10',payment=payment,production='Novo',notes='',
            items=[dict(product_id=self.top,description='Kit',qty=qty,unit_cents=5000,variants={self.paper:self.blue})])
    def balances(self):return {(r['id'],r['variant_id']):r['balance'] for r in self.s.stock()}

    def test_three_levels_repeated_leaves_cost_yield_and_variants(self):
        rows={r['material_code']:r['qty'] for r in self.s.expanded_recipe(self.top)}
        self.assertEqual(rows,{'PAP':15,'SAC':10.5})
        self.assertEqual(self.s.product_cost(self.top),(1710,[]))
        # Material cost, never the child sale price (9999).
        self.assertEqual(self.s.suggested(self.s.one('SELECT * FROM products WHERE id=?',(self.top,)))[0],3420)
        requirements=self.s.variant_requirements(self.top)
        self.assertEqual(len(requirements),1);self.assertEqual(requirements[0][0]['id'],self.paper)
        self.order()
        self.assertEqual(self.balances()[(self.paper,self.blue)],-30)
        self.assertEqual(self.balances()[(self.bag,None)],-21)

    def test_order_edit_and_delete_reverse_actual_historical_consumption(self):
        oid=self.order()
        self.product('Z10',[('PAP',8)],id=self.child,base_yield=1)
        self.order(id=oid,payment='Pago')  # payment-only edit must NOT reconsume
        self.assertEqual(self.balances()[(self.paper,self.blue)],-30)
        self.order(qty=1,id=oid)
        self.assertEqual(self.balances()[(self.paper,self.blue)],-64)
        self.assertEqual(self.balances()[(self.bag,None)],0)
        self.s.delete_order(oid)
        self.assertTrue(all(v==0 for v in self.balances().values()))

    def test_direct_and_indirect_cycle_roll_back(self):
        old=[dict(r) for r in self.s.recipe(self.child)]
        for component in (self.child,self.parent,self.top):
            with self.assertRaises(ValueError):
                self.product('Z10',[],id=self.child,components=[(component,1,'Produção')])
            self.assertEqual([dict(r) for r in self.s.recipe(self.child)],old)
        self.assertEqual(self.s.product_cost(self.top)[0],1710)

    def test_invalid_component_and_quantities_do_not_change_product(self):
        for child,qty in [(999,1),(self.child,0),(self.child,-1),(self.child,float('nan')),(self.child,float('inf'))]:
            with self.assertRaises(ValueError):self.product('A01',[],id=self.top,components=[(child,qty,'Produção')])
        self.assertEqual(len(self.s.components(self.top)),2)
        with self.assertRaises(ValueError):self.product('A01',[('PAP',float('nan'))],id=self.top,components=[])
        self.assertEqual(self.s.product_cost(self.top)[0],1710)

    def test_rename_duplicate_reopen_and_code_sort(self):
        self.product('C01',[('PAP',2),('SAC',3)],id=self.child,base_yield=2)
        self.s.save_material(id=self.paper,name='Papel',code='NOVO',pack_qty=1,pack_cents=200,unit='folha')
        self.assertEqual(self.s.components(self.parent)[0]['code'],'C01')
        copied=self.s.duplicate_product(self.top)
        self.s.toggle_product(self.top)
        self.s.close();self.s=Store(self.path)
        self.assertEqual(self.s.product_cost(copied),self.s.product_cost(self.top))
        self.assertEqual(self.s.product_cost(self.top)[0],3210)
        codes=[p['code'] for p in self.s.products()]
        self.assertEqual(codes,sorted(codes,key=str.casefold))
        self.assertEqual(self.s.all('PRAGMA foreign_key_check'),[])

    def test_missing_nested_material_blocks_order_without_side_effects(self):
        with self.s.db:self.s.db.execute("UPDATE recipes SET material_code='MISSING' WHERE product_id=?",(self.child,))
        before=self.s.all('SELECT * FROM stock_movements')
        with self.assertRaises(ValueError):self.order()
        self.assertEqual(self.s.orders(),[])
        self.assertEqual(self.s.all('SELECT * FROM stock_movements'),before)

    def test_upgrade_adds_table_without_resetting_data(self):
        # Simulate a 5.2 database, whose recipes and yields are unchanged.
        with self.s.db:self.s.db.execute('DROP TABLE product_components')
        self.s.set_cost_multiplier('2,4')
        self.s.close();self.s=Store(self.path)
        self.assertEqual(self.s.cost_multiplier(),2.4)
        self.assertEqual(self.s.product_cost(self.child)[0],130)
        self.assertEqual(len(self.s.products()),3)


class CompositionFormTests(ProductFormTests):
    def test_edit_quantity_in_both_sections_invalid_and_cancel(self):
        self.form();self.add_material(0);self.add_material(1)
        for index,new in [(0,'2,5'),(1,'3')]:
            self.trees[index].selection_set(str(index))
            with patch('app.simpledialog.askstring',return_value=new):self.actions['Editar quantidade'][index]()
        price=self.fields['PREÇO SUGERIDO (R$) • EDITÁVEL']
        self.assertEqual(price.get(),'5,19')  # (2.5 * .65 + 3 * .42) * 1.8
        with patch('app.simpledialog.askstring',return_value='0'):
            with self.assertRaises(ValueError):self.actions['Editar quantidade'][1]()
        with patch('app.simpledialog.askstring',return_value=None):self.actions['Editar quantidade'][1]()
        self.assertEqual(price.get(),'5,19')
        self.fields['NOME DO PRODUTO'].set('Editado')
        self.actions['Salvar produto'][0]()
        self.assertEqual([r['qty'] for r in self.store.recipe(self.store.products()[0]['id'])],[2.5,3])

    def test_add_product_and_edit_quantity_saves_reference(self):
        child=self.store.save_product(code='CHILD',name='Filho',markup=2,table_cents=999,recipe=[('PAP',2)])
        self.form()
        combo=self.combos[1]
        combo.set(next(label for label in combo.options['values'] if label.startswith('Produto · CHILD')))
        self.actions['Adicionar'][0]()
        self.trees[0].selection_set('0')
        with patch('app.simpledialog.askstring',return_value='3'):self.actions['Editar quantidade'][0]()
        self.assertEqual(self.fields['PREÇO SUGERIDO (R$) • EDITÁVEL'].get(),'7,02')
        self.fields['NOME DO PRODUTO'].set('Kit')
        self.actions['Salvar produto'][0]()
        parent=next(p for p in self.store.products() if p['name']=='Kit')
        self.assertEqual(self.store.components(parent['id'])[0]['component_id'],child)
        self.assertEqual(self.store.components(parent['id'])[0]['qty'],3)

if __name__=='__main__':unittest.main()
