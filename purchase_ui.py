"""Interface para registro e consulta de compras."""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from core import cents, quantity, money, fmt_qty, br_date

from visual_theme import BG,SURFACE,OLIVE,RED


class PurchaseUI:
    def purchase_page(self):
        from app import grid
        self.toolbar('Compras recebidas e pagas: entrada de insumos, atualização de preço e data.',
                     [('Nova compra',self.purchase_dialog,True),('Ver compra',self.view_purchase,False)])
        self.purchase_tree=grid(self.main,('Número','Data','Fornecedor','Total pago'),(115,120,400,150))
        for row in self.store.purchases():
            self.purchase_tree.insert('',tk.END,iid=str(row['id']),values=(f"OC{row['id']:05d}",
                br_date(row['purchase_date']),row['supplier'] or 'Não informado',money(row['total_cents'])))
        self.purchase_tree.bind('<Double-1>',lambda _:self.view_purchase())

    def view_purchase(self):
        from app import grid
        pid=self.selection(self.purchase_tree)
        if not pid:return
        order=self.store.one('SELECT * FROM purchases WHERE id=?',(pid,))
        win=self.modal(f'Compra OC{pid:05d}',820,530)
        tk.Label(win,text=f"{br_date(order['purchase_date'])}  •  {order['supplier']}  •  Total pago: {money(order['total_cents'])}",
                 bg=SURFACE,fg=OLIVE).pack(anchor='w',padx=25,pady=8)
        tk.Label(win,text=order['notes'],wraplength=740,justify='left',bg=SURFACE).pack(anchor='w',padx=25)
        tree=grid(win,('Insumo / variação','Quantidade','Unidade','Total pago'),(420,110,80,120))
        for item in self.store.purchase_items(pid):
            tree.insert('',tk.END,values=(item['description'],fmt_qty(item['qty']),item['unit'],money(item['total_cents'])))

    def purchase_dialog(self):
        from app import button, field, grid
        win=self.modal('Nova ordem de compra',880,640)
        tk.Label(win,text='Data: '+date.today().strftime('%d/%m/%Y')+' • Compra recebida e paga',
                 bg=SURFACE,fg=OLIVE).pack(anchor='w',padx=26)
        form=tk.Frame(win,bg=SURFACE);form.pack(fill='x',padx=16)
        for i in range(2):form.grid_columnconfigure(i,weight=1)
        supplier=field(form,'FORNECEDOR (OPCIONAL)',0)
        notes=field(form,'OBSERVAÇÕES',0,col=1)
        tk.Label(win,text='Quantidade na unidade do insumo: ex. 2 pacotes de 100 folhas = 200 un. Valor = total pago pela linha.',
                 bg=SURFACE,fg=OLIVE,wraplength=820,justify='left').pack(anchor='w',padx=26,pady=12)
        chooser=tk.Frame(win,bg=SURFACE);chooser.pack(fill='x',padx=26)
        chooser.grid_columnconfigure(0,weight=1)
        for col,label in enumerate(('INSUMO / VARIAÇÃO / UNIDADE','QUANTIDADE','TOTAL PAGO (R$)')):
            tk.Label(chooser,text=label,bg=SURFACE,fg=OLIVE).grid(row=0,column=col,sticky='w')
        mapping={}
        for material in self.store.materials():
            if not material['active']:continue
            variants=self.store.variants(material['id'])
            options=[(v['id'],v['name']) for v in variants if v['active']] if variants else [(None,'Padrão')]
            for vid,name in options:
                label=f"{material['code']} · {material['name']} · {name} [{material['unit']}]"
                mapping[label]=(material,vid)
        combo=ttk.Combobox(chooser,values=list(mapping),width=40)
        combo.grid(row=1,column=0,sticky='ew',padx=(0,8))
        combo.bind('<KeyRelease>',lambda _:combo.configure(values=[v for v in mapping if combo.get().casefold() in v.casefold()]))
        qty=ttk.Entry(chooser,width=12);qty.insert(0,'1');qty.grid(row=1,column=1,padx=4)
        paid=ttk.Entry(chooser,width=14);paid.grid(row=1,column=2,padx=4)
        footer=tk.Frame(win,bg=SURFACE);footer.pack(side='bottom',fill='x',padx=26,pady=16)
        total=tk.StringVar(value='Total: R$ 0,00')
        tk.Label(footer,textvariable=total,bg=SURFACE,fg=RED,font=('Segoe UI',12,'bold')).pack(side='left')
        tree=grid(win,('Insumo / variação','Qtd','Unidade','Total pago'),(420,80,70,110))
        items=[]
        def redraw():
            tree.delete(*tree.get_children())
            for i,item in enumerate(items):
                tree.insert('',tk.END,iid=str(i),values=(item['label'],fmt_qty(item['qty']),item['unit'],money(item['total_cents'])))
            total.set('Total: '+money(sum(i['total_cents'] for i in items)))
        def add():
            try:
                if combo.get() not in mapping:raise ValueError('Selecione um insumo e sua variação na lista.')
                material,vid=mapping[combo.get()]
                items.append(dict(material_id=material['id'],variant_id=vid,qty=quantity(qty.get()),
                                  total_cents=cents(paid.get()),label=combo.get(),unit=material['unit']))
                redraw();paid.delete(0,tk.END)
            except ValueError as exc:self.fail(exc,win)
        button(chooser,'Adicionar',add,False).grid(row=1,column=3,padx=4)
        def remove():
            selected=tree.selection()
            if selected:items.pop(int(selected[0]));redraw()
        button(footer,'Remover item',remove,False).pack(side='left',padx=15)
        saved=False
        def save():
            nonlocal saved
            if saved:return
            if not items:
                self.fail(ValueError('Adicione ao menos um insumo.'),win);return
            if not messagebox.askyesno('Confirmar compra',
                'Registrar a compra como recebida e paga? Isso dará entrada no estoque e atualizará os preços e a data dos insumos.',parent=win):return
            try:
                self.store.save_purchase(items=items,supplier=supplier.get(),notes=notes.get())
            except (ValueError,ArithmeticError,sqlite3.Error) as exc:
                self.fail(exc,win);return
            saved=True
            win.destroy();self.render()
        button(footer,'Confirmar compra',save).pack(side='right')
