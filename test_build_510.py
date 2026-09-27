"""Regressões da limpeza única e do formulário simplificado (sem display)."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from core import Store
from fresh_start import prepare_database, RESET_KEY


class ResetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'marte.db'

    def tearDown(self):self.tmp.cleanup()

    def seed(self):
        s=Store(self.path)
        s.save_customer(name='Cliente antigo')
        mid=s.save_material(name='Papel',code='PAP',unit='folha',pack_qty=1,pack_cents=100,
                            variants=['Branco'])
        vid=s.variants(mid)[0]['id']
        pid=s.save_product(name='Produto',code='PRO',markup=2,table_cents=None,recipe=[('PAP',1)])
        s.save_purchase(supplier='Fornecedor',items=[dict(material_id=mid,variant_id=vid,qty=10,total_cents=1000)])
        s.save_order(customer='Cliente antigo',due_date='2026-10-01',payment='Pendente',production='Novo',notes='',
                     items=[dict(product_id=pid,description='Produto',qty=1,unit_cents=200,variants={mid:vid})])
        s.close()

    def test_backup_full_reset_and_second_start_preserves_new_data(self):
        self.seed()
        folder=self.path.parent/'backups';folder.mkdir()
        old=folder/'backup_anterior.db';old.write_bytes(b'preservar')
        backup=prepare_database(self.path)
        self.assertTrue(backup.is_file())
        with closing(sqlite3.connect(backup)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM orders').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM purchases').fetchone()[0],1)
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        with closing(sqlite3.connect(self.path)) as db:
            for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                if not name.startswith('sqlite_') and name!='app_migrations':
                    self.assertEqual(db.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0],0,name)
            self.assertEqual(db.execute('SELECT name FROM app_migrations').fetchone()[0],RESET_KEY)
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
        s=Store(self.path);s.save_customer(name='Cliente novo');s.close()
        self.assertIsNone(prepare_database(self.path))
        s=Store(self.path)
        self.assertEqual(s.customers()[0]['name'],'Cliente novo');s.close()
        self.assertEqual(len(list(folder.glob('antes_reset*'))),1)
        self.assertEqual(old.read_bytes(),b'preservar')

    def test_empty_installation_stays_empty_and_marks_reset(self):
        self.assertIsNone(prepare_database(self.path))
        s=Store(self.path)
        self.assertEqual(s.products(),[]);self.assertEqual(s.materials(),[])
        s.save_customer(name='Novo');s.close()
        self.assertIsNone(prepare_database(self.path))
        s=Store(self.path);self.assertEqual(len(s.customers()),1);s.close()

    def test_backup_failure_never_deletes_data(self):
        self.seed()
        (self.path.parent/'backups').write_text('folder blocked')
        with self.assertRaises(OSError):prepare_database(self.path)
        s=Store(self.path)
        self.assertEqual(len(s.customers()),1);self.assertEqual(len(s.products()),1);s.close()

    def test_sql_failure_rolls_back_all_deletions_and_marker(self):
        self.seed()
        # The SQLite context manager does not close the file handle on Windows.
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TRIGGER prevent_reset BEFORE DELETE ON orders BEGIN SELECT RAISE(ABORT,'blocked'); END")
        with self.assertRaises(sqlite3.IntegrityError):prepare_database(self.path)
        s=Store(self.path)
        self.assertEqual(len(s.materials()),1);self.assertEqual(len(s.products()),1)
        self.assertEqual(len(s.customers()),1)
        self.assertFalse(s.one("SELECT 1 FROM sqlite_master WHERE name='app_migrations'"));s.close()


class Variable:
    def __init__(self,*args,**kwargs):self.value='';self.callbacks=[]
    def get(self):return self.value
    def set(self,value):
        self.value=str(value)
        for callback in self.callbacks:callback(None,None,None)
    def trace_add(self,mode,callback):self.callbacks.append(callback)


class Widget:
    def __init__(self,*args,**kwargs):
        self.options=kwargs;self.value='';self.rows={};self.selected=()
    def pack(self,*a,**k):pass
    def grid(self,*a,**k):pass
    def grid_columnconfigure(self,*a,**k):pass
    def columnconfigure(self,*a,**k):pass
    def rowconfigure(self,*a,**k):pass
    def configure(self,**kwargs):self.options.update(kwargs)
    def bind(self,*a,**k):pass
    def destroy(self):pass
    def grab_set(self):pass
    def heading(self,*a,**k):pass
    def column(self,*a,**k):pass
    def yview(self,*a,**k):pass
    def set(self,value):self.value=value
    def get(self):return self.options['textvariable'].get() if 'textvariable' in self.options else self.value
    def insert(self,*args,**kwargs):
        if 'iid' in kwargs:self.rows[kwargs['iid']]=kwargs['values']
        else:self.value=args[-1]
    def get_children(self):return tuple(self.rows)
    def delete(self,*items):
        for item in items:self.rows.pop(item,None)
    def selection(self):return self.selected


class ProductFormTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(Path(self.tmp.name)/'marte.db')
        self.store.save_material(name='Papel',code='PAP',unit='folha',pack_qty=1,pack_cents=65,category='Produção')
        self.store.save_material(name='Saco',code='SAC',unit='un',pack_qty=1,pack_cents=42,category='Embalagem')

    def tearDown(self):self.store.close();self.tmp.cleanup()

    def form(self,p=None):
        # Exercise the actual dialog callbacks without a graphical display.
        import app
        from contextlib import ExitStack
        stack=ExitStack();self.addCleanup(stack.close)
        self.fields={};self.actions={};self.combos=[];self.labels=[];self.helps=[]
        def field(parent,label,row,default='',col=0,**kwargs):
            var=kwargs.get('variable') or Variable();var.set(default)
            self.fields[label]=var
            self.helps.append(kwargs.get('help_text'))
            return var
        def button(parent,text,command,*args):
            self.actions.setdefault(text,[]).append(command);return Widget()
        def combo(*a,**k):
            w=Widget(*a,**k);self.combos.append(w);return w
        def label(*a,**k):
            w=Widget(*a,**k);self.labels.append(w);return w
        def area(*a,**k):
            w=Widget();w.content=Widget();return w
        for target,replacement in [('tk.Frame',Widget),('tk.LabelFrame',Widget),('tk.Label',label),
                ('tk.StringVar',Variable),('ttk.Combobox',combo),('ttk.Entry',Widget),('ttk.Scrollbar',Widget),
                ('ScrollArea',area),('StripedTreeview',Widget),('field',field),('button',button),('help_icon',lambda *a:Widget())]:
            stack.enter_context(patch('app.'+target,replacement))
        self.ui=app.ERP.__new__(app.ERP);self.ui.store=self.store
        self.ui.modal=lambda *a:Widget();self.ui.render=lambda:None
        self.ui.fail=lambda exc,win:(_ for _ in ()).throw(exc)
        self.ui.product_dialog(p)

    def add_material(self,index):
        combo=self.combos[index];combo.set(combo.options['values'][0]);self.actions['Adicionar'][index]()

    def test_live_sum_multiplier_edit_save_and_order_consumption(self):
        self.form()
        self.assertNotIn('PRODUTO BASE • PRODUZ QUANTAS UNIDADES?',self.fields)
        self.assertTrue(all(self.helps))
        self.add_material(0);self.add_material(1)
        price=self.fields['PREÇO SUGERIDO (R$) • EDITÁVEL']
        factor=self.fields['MULTIPLICADOR SOBRE O CUSTO']
        self.assertEqual(price.get(),'1,93')  # (0.65 + 0.42) * 1.8
        factor.set('2,5');self.assertEqual(price.get(),'2,68')
        price.set('3,50')
        self.fields['NOME DO PRODUTO'].set('Produto')
        self.fields['CÓDIGO DO PRODUTO'].set('PRO')
        self.actions['Salvar produto'][0]()
        p=self.store.products()[0]
        self.assertEqual((p['base_yield'],p['table_cents']),(1,350))
        self.assertEqual(self.store.product_cost(p['id'])[0],107)
        self.store.save_order(customer='Novo',due_date='2026-10-01',payment='Pendente',production='Novo',notes='',
            items=[dict(product_id=p['id'],description='Produto',qty=2,unit_cents=p['table_cents'])])
        self.assertTrue(all(r['balance']==-2 for r in self.store.stock()))

    def test_edit_preserves_manual_price_until_cost_or_factor_changes(self):
        pid=self.store.save_product(name='Produto',code='PRO',markup=1.8,table_cents=999,recipe=[('PAP',1)])
        self.form(self.store.products()[0])
        price=self.fields['PREÇO SUGERIDO (R$) • EDITÁVEL']
        self.assertEqual(price.get(),'9,99')
        self.fields['TAMANHO'].set('A4');self.assertEqual(price.get(),'9,99')
        self.fields['MULTIPLICADOR SOBRE O CUSTO'].set('2')
        self.assertEqual(price.get(),'1,30')

    def test_invalid_factor_keeps_cost_visible_and_prevents_save(self):
        self.form();self.add_material(0)
        factor=self.fields['MULTIPLICADOR SOBRE O CUSTO']
        for invalid in ('','abc','nan','inf','0,5'):
            factor.set(invalid)
            self.assertTrue(any('Custo total: R$ 0,65' in w.options.get('text','') for w in self.labels))
            with self.assertRaises(ValueError):self.actions['Salvar produto'][0]()
        factor.set('2');self.assertEqual(self.fields['PREÇO SUGERIDO (R$) • EDITÁVEL'].get(),'1,30')


if __name__=='__main__':unittest.main()
