"""Configuração de acabamentos reutilizáveis e preço por folha A4."""
import tkinter as tk
from tkinter import ttk
from core import money,cents,quantity,fmt_qty
from visual_theme import SURFACE,OLIVE,MUTED


def configure_finishes(app,parent=None):
    from app import field,button
    app.store.ensure_finish_catalog()
    win=app.modal('Configurar acabamentos',850,640)
    if parent:win.transient(parent)
    tk.Label(win,text='Vincule o BOPP Brilhante que já está nas receitas. Cada acabamento deve usar um insumo diferente.\n'
        'Preço da embalagem ÷ folhas A4 úteis = custo por folha. Adicional é por peça vendida.\n'
        'Para um rolo de 50 m, informe seu valor e o número de folhas úteis obtidas no corte.',
        bg=SURFACE,fg=MUTED,justify='left',wraplength=790).pack(anchor='w',padx=24,pady=8)
    finishes=app.store.finishes()
    linked={f['material_id'] for f in finishes}
    materials={f"{m['code']} · {m['name']}"+(' (inativo)' if not m['active'] else ''):m
        for m in app.store.materials() if m['active'] or m['id'] in linked}
    rows=[]
    for finish in finishes:
        box=tk.LabelFrame(win,text=finish['name'],bg=SURFACE,fg=OLIVE)
        box.pack(fill='x',padx=24,pady=4)
        for col in range(3):box.columnconfigure(col,weight=1)
        selected=tk.StringVar(value=next(k for k,m in materials.items() if m['id']==finish['material_id']))
        combo=ttk.Combobox(box,values=list(materials),textvariable=selected,state='readonly')
        combo.grid(row=0,column=0,columnspan=3,sticky='ew',padx=10,pady=5)
        qty=field(box,'FOLHAS A4 POR EMBALAGEM',1,fmt_qty(finish['pack_qty']),0)
        price=field(box,'VALOR DA EMBALAGEM / ROLO (R$)',1,f"{finish['pack_cents']/100:.2f}",1)
        extra=field(box,'ADICIONAL POR PEÇA (R$)',1,f"{finish['extra_cents']/100:.2f}",2)
        if finish['key']=='brilhante':extra.configure(state='readonly')
        def load(_=None,var=selected,q=qty,p=price):
            m=materials[var.get()];q.delete(0,tk.END);q.insert(0,fmt_qty(m['pack_qty']))
            p.delete(0,tk.END);p.insert(0,f"{m['pack_cents']/100:.2f}")
        combo.bind('<<ComboboxSelected>>',load)
        rows.append((finish['key'],selected,qty,price,extra))
    def save():
        try:
            values=[dict(key=k,material_id=materials[v.get()]['id'],pack_qty=quantity(q.get()),
                pack_cents=cents(p.get()),extra_cents=cents(e.get())) for k,v,q,p,e in rows]
            app.store.configure_finishes(values)
        except ValueError as exc:app.fail(exc,win);return
        win.destroy()
    button(win,'Salvar configuração',save).pack(side='bottom',anchor='e',padx=24,pady=10)
    win.wait_window()
    if parent and parent.winfo_exists():parent.grab_set()
