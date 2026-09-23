"""Papéis de Marte | ERP local com interface Tkinter."""
from __future__ import annotations

import sqlite3
import math
import calendar
import os
import queue
import threading
import time
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from automatic_backup import AutomaticBackup
from core import (Store, asset, automatic_code, br_date, cents, data_directory,
                  export_order_pdf, export_report_pdf, filter_orders, fmt_qty, money, parse_date, quantity)
from updater import check_and_stage, launch_cached, read_config

BG = '#FFF8F0'
SURFACE = '#FFFFFF'
CREAM = '#F7E9DB'
RED = '#A7463E'
RED_DARK = '#84352F'
OLIVE = '#48452C'
GOLD = '#BD8738'
MUTED = '#736A61'
MONTHS = ('Total','Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho',
          'Agosto','Setembro','Outubro','Novembro','Dezembro')


def field(parent, label, row, default='', col=0, width=28, variable=None):
    tk.Label(parent,text=label,bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold')).grid(row=row,column=col,sticky='w',padx=10,pady=(12,3))
    entry=ttk.Entry(parent,width=width,textvariable=variable)
    entry.grid(row=row+1,column=col,sticky='ew',padx=10,pady=(0,3))
    if variable is None:entry.insert(0,str(default if default is not None else ''))
    else:variable.set(str(default if default is not None else ''))
    return entry


def button(parent,text,command,primary=True):
    return tk.Button(parent,text=text,command=command,bg=RED if primary else CREAM,
                     fg='white' if primary else OLIVE,activebackground=RED_DARK if primary else '#EBD6C1',
                     activeforeground='white' if primary else OLIVE,relief='flat',bd=0,
                     cursor='hand2',font=('Segoe UI',10,'bold'),padx=16,pady=9)


def grid(parent, columns, widths):
    box=tk.Frame(parent,bg=SURFACE)
    box.pack(fill='both',expand=True,padx=26,pady=(12,23))
    table=tk.Frame(box,bg=SURFACE)
    table.pack(fill='both',expand=True)
    tree=ttk.Treeview(table,columns=columns,show='headings',selectmode='browse')
    for column,width in zip(columns,widths):
        tree.heading(column,text=column)
        tree.column(column,width=width,minwidth=65,anchor='w',stretch=True)
    scrollbar=ttk.Scrollbar(table,orient='vertical',command=tree.yview)
    horizontal=ttk.Scrollbar(box,orient='horizontal',command=tree.xview)
    tree.configure(yscrollcommand=scrollbar.set,xscrollcommand=horizontal.set)
    tree.pack(side='left',fill='both',expand=True)
    scrollbar.pack(side='right',fill='y')
    horizontal.pack(fill='x')
    return tree


def pick_date(parent, entry):
    """Choose a date without requiring internet access or another package."""
    try:chosen=date.fromisoformat(parse_date(entry.get()))
    except ValueError:chosen=date.today()
    popup=tk.Toplevel(parent)
    popup.title('Escolher data de entrega')
    popup.configure(bg=SURFACE)
    popup.resizable(False,False)
    popup.transient(parent)
    popup.update_idletasks()
    x=min(entry.winfo_rootx(),popup.winfo_screenwidth()-325)
    y=min(entry.winfo_rooty()+entry.winfo_height()+5,popup.winfo_screenheight()-320)
    popup.geometry(f'305x290+{max(0,x)}+{max(0,y)}')
    panel=tk.Frame(popup,bg=SURFACE)
    panel.pack(fill='both',expand=True,padx=12,pady=12)
    for column in range(7):panel.grid_columnconfigure(column,weight=1)
    title=tk.Label(panel,bg=SURFACE,fg=OLIVE,font=('Segoe UI',12,'bold'))
    title.grid(row=0,column=1,columnspan=5,pady=(1,11))
    state=[chosen.year,chosen.month]
    def draw():
        title.config(text=f'{MONTHS[state[1]]} {state[0]}')
        for child in panel.grid_slaves():
            if int(child.grid_info()['row'])>=2:child.destroy()
        for column,name in enumerate(('Seg','Ter','Qua','Qui','Sex','Sáb','Dom')):
            tk.Label(panel,text=name,bg=SURFACE,fg=MUTED,font=('Segoe UI',9,'bold')).grid(row=2,column=column,pady=3)
        for row,week in enumerate(calendar.monthcalendar(*state),start=3):
            for column,day in enumerate(week):
                if not day:continue
                def select(value=day):
                    entry.delete(0,tk.END)
                    entry.insert(0,date(state[0],state[1],value).strftime('%d/%m/%Y'))
                    popup.destroy()
                tk.Button(panel,text=str(day),command=select,relief='flat',bd=0,cursor='hand2',
                          bg=RED if (state[0],state[1],day)==(chosen.year,chosen.month,chosen.day) else BG,
                          fg='white' if (state[0],state[1],day)==(chosen.year,chosen.month,chosen.day) else OLIVE,
                          font=('Segoe UI',9),width=3,pady=3).grid(row=row,column=column,pady=1)
    def move(delta):
        month=state[0]*12+state[1]-1+delta
        state[:]=[month//12,(month%12)+1]
        draw()
    button(panel,'‹',lambda:move(-1),False).grid(row=0,column=0)
    button(panel,'›',lambda:move(1),False).grid(row=0,column=6)
    draw()
    popup.grab_set()
    popup.wait_window()
    if parent.winfo_exists():parent.grab_set()


class ERP:
    def __init__(self,root):
        self.root=root
        workbook=asset('Precificação.xlsx')
        self.store=Store(data_directory()/'marte.db',workbook if workbook.is_file() else None)
        root.title('Papéis de Marte • ERP offline')
        root.geometry('1290x790')
        root.minsize(1020,650)
        root.configure(bg=BG)
        self.style=ttk.Style(root)
        self.style.theme_use('clam')
        self.style.configure('Treeview',font=('Segoe UI',10),rowheight=31,background=SURFACE,
                             fieldbackground=SURFACE,foreground=OLIVE,borderwidth=0)
        self.style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),background=CREAM,
                             foreground=OLIVE,relief='flat',padding=8)
        self.style.map('Treeview',background=[('selected','#F2D2C0')],foreground=[('selected',OLIVE)])
        self.style.configure('TEntry',padding=6)
        self.style.configure('TCombobox',padding=5)
        self.logo=tk.PhotoImage(file=str(asset('logo.png'))).subsample(2,2)
        self.automatic_backup=AutomaticBackup(data_directory())
        self.backup_status=tk.StringVar(value='Backup: aguardando')
        self._backed_up_changes=-1
        self._backed_up_day=None
        self._cloud_retry_at=0
        self._cloud_error=False
        self._closing=False
        self._close_results=queue.Queue()
        self.page='Papéis de Marte'
        self.calendar_month=date.today().replace(day=1)
        self.calendar_selected=date.today()
        self.order_filters={}
        self.material_filters={}
        self.report_month=date.today().month
        self.report_year=date.today().year
        self._navigating=False
        self.search=tk.StringVar()
        self.search.trace_add('write',lambda *_: self.render() if self.page in ('Insumos','Produtos') and not self._navigating else None)
        self.build_shell();self.render()
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.update_events=queue.Queue()
        self.update_config=read_config(asset('update_config.json'))
        if self.update_config.get('manifest_url'):
            root.after(1500,self.check_updates)
        root.after(2500,self.check_automatic_backup)

    def close(self):
        if self._closing:return
        self._closing=True
        self.store.db.commit()
        dialog=tk.Toplevel(self.root)
        dialog.title('Cópia de segurança')
        dialog.configure(bg=SURFACE)
        dialog.resizable(False,False)
        dialog.geometry('370x150')
        dialog.transient(self.root)
        dialog.protocol('WM_DELETE_WINDOW',lambda:None)
        tk.Label(dialog,text='Backup sendo realizado',bg=SURFACE,fg=OLIVE,
                 font=('Segoe UI',14,'bold')).pack(pady=(20,8))
        tk.Label(dialog,text='Aguarde a cópia terminar antes de fechar.',bg=SURFACE,fg=MUTED,
                 font=('Segoe UI',9)).pack()
        progress=ttk.Progressbar(dialog,mode='indeterminate',length=290)
        progress.pack(pady=(16,10));progress.start(12)
        dialog.grab_set()
        started=time.monotonic()
        def worker():
            try:self._close_results.put((self.automatic_backup.create(self.store.path),None))
            except (OSError,ValueError,sqlite3.Error) as exc:self._close_results.put((None,str(exc)))
        threading.Thread(target=worker,daemon=True).start()
        def finish():
            try:result,error=self._close_results.get_nowait()
            except queue.Empty:
                self.root.after(80,finish)
                return
            elapsed=time.monotonic()-started
            if elapsed<0.8:
                self.root.after(max(1,int((0.8-elapsed)*1000)),finish_result,result,error)
            else:finish_result(result,error)
        def finish_result(result,error):
            progress.stop();dialog.destroy()
            if error:
                self._closing=False
                if messagebox.askyesno('Falha no backup',
                    f'Não foi possível gerar a cópia: {error}\n\nFechar mesmo assim?',parent=self.root):
                    self.store.close();self.root.destroy()
                return
            if result.selected_error:
                messagebox.showwarning('Cópia na pasta não concluída',
                    'O backup local foi salvo, mas a pasta escolhida não recebeu a cópia. '
                    f'Confira a sincronização e o espaço disponível.\n\nDetalhes: {result.selected_error}',parent=self.root)
            self.store.close();self.root.destroy()
        self.root.after(80,finish)

    def check_automatic_backup(self):
        if self._closing:return
        changed=self._backed_up_changes!=self.store.db.total_changes
        new_day=self._backed_up_day!=date.today()
        retry=self._cloud_error and time.monotonic()-self._cloud_retry_at>300
        if changed or new_day or retry:self.run_automatic_backup()
        self.root.after(30000,self.check_automatic_backup)

    def run_automatic_backup(self):
        try:
            result=self.automatic_backup.create(self.store.path)
            self._backed_up_changes=self.store.db.total_changes
            self._backed_up_day=date.today()
            self._cloud_error=bool(result.selected_error)
            self._cloud_retry_at=time.monotonic()
            stamp=time.strftime('%d/%m %H:%M')
            if result.selected_error:
                self.backup_status.set(f'Backup local: {stamp} • revisar pasta')
            elif result.selected_path:
                self.backup_status.set(f'Cópia na pasta: {stamp}')
            else:
                self.backup_status.set(f'Backup local: {stamp}')
            return result
        except (OSError,ValueError,sqlite3.Error) as exc:
            self.backup_status.set('Falha no backup • confira a pasta')
            return None

    def choose_backup_folder(self):
        initial=self.automatic_backup.folder
        if initial is None or not initial.is_dir():
            initial=next((Path(value) for key in ('OneDriveCommercial','OneDrive','OneDriveConsumer')
                          if (value:=os.environ.get(key)) and Path(value).is_dir()),Path.home())
        folder=filedialog.askdirectory(parent=self.root,initialdir=str(initial),
                                       title='Escolha a pasta para as cópias automáticas')
        if not folder:return
        try:self.automatic_backup.select_folder(folder)
        except (OSError,ValueError) as exc:
            messagebox.showerror('Pasta indisponível',str(exc),parent=self.root)
            return
        result=self.run_automatic_backup()
        if result and result.selected_path:
            messagebox.showinfo('Backup configurado',
                f'Cópia salva em:\n{result.selected_path}\n\n'
                'Se essa pasta estiver no OneDrive ou Google Drive, confira o ícone de sincronização para saber quando a cópia chegou à nuvem.',
                parent=self.root)
        else:
            messagebox.showwarning('Confira a pasta',
                'A cópia local foi mantida. Verifique se a pasta escolhida está disponível.',parent=self.root)

    def check_updates(self):
        def worker():
            try:
                version=check_and_stage(self.update_config,data_directory())
                if version:self.update_events.put(version)
            except Exception:
                # Falha de conexão não deve bloquear o trabalho offline.
                pass
        threading.Thread(target=worker,daemon=True).start()
        self.poll_updates()

    def poll_updates(self):
        try:version=self.update_events.get_nowait()
        except queue.Empty:self.root.after(1000,self.poll_updates)
        else:
            self.update_status.config(text=f'Versão {version} pronta · abra o aplicativo novamente')

    def build_shell(self):
        side=tk.Frame(self.root,bg=OLIVE,width=224)
        side.pack(side='left',fill='y');side.pack_propagate(False)
        tk.Label(side,image=self.logo,bg=OLIVE).pack(pady=(24,0))
        tk.Label(side,text='PAPÉIS DE MARTE',bg=OLIVE,fg='#FFF8F0',
                 font=('Segoe UI',14,'bold')).pack(pady=(3,2))
        tk.Label(side,text='Thayna Donadei',bg=OLIVE,fg='#E8CDA7',
                 font=('Segoe UI',9)).pack(pady=(0,32))
        for name,icon in [('Papéis de Marte','⌂'),('Insumos','◈'),('Produtos','▦'),('Pedidos','▤'),
                          ('Calendário','▦'),('Estoque','◉'),('Relatórios','▥')]:
            tk.Button(side,text=f'  {icon}    {name}',anchor='w',command=lambda n=name:self.navigate(n),
                      bg=OLIVE,fg='white',activebackground='#686344',activeforeground='white',
                      relief='flat',bd=0,cursor='hand2',font=('Segoe UI',11),padx=22,pady=14).pack(fill='x',pady=2)
        tk.Frame(side,bg=OLIVE).pack(fill='both',expand=True)
        self.update_status=tk.Label(side,text='',bg=OLIVE,fg='#F1D7AA',wraplength=190,
                                    justify='left',font=('Segoe UI',9))
        self.update_status.pack(fill='x',padx=19,pady=8)
        tk.Button(side,text='↧    Salvar cópia dos dados',anchor='w',command=self.backup,
                  bg=OLIVE,fg='#F1D7AA',activebackground='#686344',activeforeground='white',
                  relief='flat',bd=0,cursor='hand2',font=('Segoe UI',9),padx=22,pady=16).pack(fill='x')
        self.main=tk.Frame(self.root,bg=BG)
        self.main.pack(side='left',fill='both',expand=True)

    def navigate(self,page):
        self._navigating=True;self.page=page;self.search.set('');self._navigating=False;self.render()

    def render(self):
        for w in self.main.winfo_children():w.destroy()
        head=tk.Frame(self.main,bg=BG)
        head.pack(fill='x',padx=26,pady=(24,12))
        tk.Label(head,text=self.page,bg=BG,fg=OLIVE,font=('Segoe UI',24,'bold')).pack(side='left')
        tk.Label(head,text=date.today().strftime('%d/%m/%Y'),bg=BG,fg=MUTED,
                 font=('Segoe UI',10)).pack(side='right')
        tk.Button(head,text='📁',command=self.choose_backup_folder,
                  bg=CREAM,fg=OLIVE,activebackground='#EBD6C1',relief='flat',bd=0,
                  cursor='hand2',font=('Segoe UI',12),padx=7,pady=3).pack(side='right',padx=(0,12))
        tk.Label(head,textvariable=self.backup_status,bg=BG,fg=MUTED,
                 font=('Segoe UI',9)).pack(side='right',padx=(0,9))
        if self.page=='Papéis de Marte':self.home()
        elif self.page=='Insumos':self.material_page()
        elif self.page=='Produtos':self.product_page()
        elif self.page=='Pedidos':self.order_page()
        elif self.page=='Calendário':self.calendar_page()
        elif self.page=='Estoque':self.stock_page()
        else:self.report_page()

    def toolbar(self,description,actions):
        bar=tk.Frame(self.main,bg=BG)
        bar.pack(fill='x',padx=26,pady=(0,7))
        tk.Label(bar,text=description,bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
        for label,cmd,primary in reversed(actions):
            button(bar,label,cmd,primary).pack(side='right',padx=(8,0))
        return bar

    def selection(self,tree):
        selection=tree.selection()
        if not selection:
            messagebox.showinfo('Selecione um registro','Selecione uma linha da lista.',parent=self.root)
            return None
        return int(selection[0])

    def home(self):
        d=self.store.dashboard()
        tk.Label(self.main,text='Sua Papelaria de Outro Planeta',bg=BG,fg=RED,
                 font=('Segoe UI',14)).pack(anchor='w',padx=26,pady=(0,18))
        cards=tk.Frame(self.main,bg=BG);cards.pack(fill='x',padx=22)
        for i,(label,value) in enumerate([
            ('INSUMOS',str(d['materials'])),('PRODUTOS',str(d['products'])),
            ('PEDIDOS EM ABERTO',str(d['open'])),('PEDIDOS REGISTRADOS',str(d['orders']))
        ]):
            card=tk.Frame(cards,bg=SURFACE,highlightbackground='#EAD9CC',highlightthickness=1)
            card.grid(row=0,column=i,padx=5,sticky='nsew')
            cards.grid_columnconfigure(i,weight=1)
            tk.Label(card,text=label,bg=SURFACE,fg=MUTED,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=17,pady=(18,7))
            tk.Label(card,text=value,bg=SURFACE,fg=RED,font=('Segoe UI',27,'bold')).pack(anchor='w',padx=17,pady=(0,18))
        detail=tk.Frame(self.main,bg=BG);detail.pack(fill='x',padx=26,pady=24)
        for i,(label,value) in enumerate([('TOTAL DOS PEDIDOS COM PREÇO DEFINIDO',money(d['revenue'])),
                                           ('PREÇO MÉDIO POR UNIDADE VENDIDA',money(d['mean_item_price']))]):
            card=tk.Frame(detail,bg=CREAM)
            card.grid(row=0,column=i,sticky='nsew',padx=(0,10) if i==0 else (10,0))
            detail.grid_columnconfigure(i,weight=1)
            tk.Label(card,text=label,bg=CREAM,fg=MUTED,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=18,pady=(15,7))
            tk.Label(card,text=value,bg=CREAM,fg=OLIVE,font=('Segoe UI',18,'bold')).pack(anchor='w',padx=18,pady=(0,16))
        tk.Label(self.main,text='Próximas entregas e pedidos em aberto',bg=BG,fg=OLIVE,
                 font=('Segoe UI',14,'bold')).pack(anchor='w',padx=26,pady=(0,5))
        tree=grid(self.main,('Pedido','Cliente','Entrega','Produção','Total'),(105,250,130,180,120))
        for o in d['due']:
            tree.insert('',tk.END,values=(o['number'],o['customer'],br_date(o['due_date']),o['production'],
                                         money(o['total_cents']) if not o['unpriced'] else 'A definir'))
        tree.bind('<Double-1>',lambda _:self.navigate('Pedidos'))

    def filter_bar(self):
        bar=tk.Frame(self.main,bg=BG);bar.pack(fill='x',padx=26,pady=(0,3))
        tk.Label(bar,text='Buscar:',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
        ttk.Entry(bar,textvariable=self.search,width=40).pack(side='left',padx=9)

    def material_page(self):
        self.toolbar('Preço da embalagem ÷ quantidade = custo por unidade.',
                     [('Novo insumo',lambda:self.material_dialog(),True),
                      ('Editar',lambda:self.edit_material(),False),
                      ('Ativar / inativar',lambda:self.toggle_material(),False)])
        filters=tk.Frame(self.main,bg=BG);filters.pack(fill='x',padx=26,pady=5)
        variables={}
        for i,(key,label) in enumerate((('name','Nome / código'),('size','Tamanho'),
                                       ('grammage','Gramatura'),('variant','Variação'),('state','Estado'))):
            filters.grid_columnconfigure(i,weight=1)
            tk.Label(filters,text=label,bg=BG,fg=MUTED).grid(row=0,column=i,sticky='w',padx=3)
            var=tk.StringVar(value=self.material_filters.get(key,''));variables[key]=var
            entry=(ttk.Combobox(filters,textvariable=var,values=('','Ativo','Inativo'),state='readonly',width=10)
                   if key=='state' else ttk.Entry(filters,textvariable=var,width=14))
            entry.grid(row=1,column=i,sticky='ew',padx=3)
        self.tree=grid(self.main,('Código','Insumo','Tamanho','Gramatura','Variações','Embalagem','Preço','Custo/un.','Estado','Data do preço'),
                       (110,155,75,75,165,100,95,100,70,110))
        def populate(*_):
            self.material_filters={key:var.get() for key,var in variables.items()}
            self.tree.delete(*self.tree.get_children())
            for m in self.store.materials():
                names=', '.join(v['name'] for v in self.store.variants(m['id'],active_only=True))
                state='Ativo' if m['active'] else 'Inativo'
                values={'name':m['code']+' '+m['name'],'size':m['size'],
                        'grammage':m['grammage'],'variant':names,'state':state}
                if any(value.strip().casefold() not in values[key].casefold()
                       for key,value in self.material_filters.items() if key!='state'):continue
                if self.material_filters['state'] and self.material_filters['state']!=state:continue
                unit_cost=m['pack_cents']/m['pack_qty']
                self.tree.insert('',tk.END,iid=str(m['id']),values=(m['code'],m['name'],m['size'],m['grammage'],names,
                    fmt_qty(m['pack_qty'])+' '+m['unit'],money(m['pack_cents']),
                    f'R$ {unit_cost/100:.4f}'.replace('.',','),state,br_date(m['price_date'])))
        def clear():
            for var in variables.values():var.set('')
        button(filters,'Limpar',clear,False).grid(row=1,column=5,padx=5)
        for var in variables.values():var.trace_add('write',populate)
        populate()
        self.tree.bind('<Double-1>',lambda _:self.edit_material())

    def edit_material(self):
        id=self.selection(self.tree)
        if id:self.material_dialog(self.store.one('SELECT * FROM materials WHERE id=?',(id,)))

    def toggle_material(self):
        id=self.selection(self.tree)
        if id:self.store.toggle_material(id);self.render()

    def modal(self,title,width=670,height=530):
        win=tk.Toplevel(self.root);win.title(title);win.configure(bg=SURFACE)
        win.geometry(f'{width}x{height}');win.minsize(width,min(height,480))
        win.transient(self.root);win.grab_set()
        tk.Label(win,text=title,bg=SURFACE,fg=OLIVE,font=('Segoe UI',18,'bold')).pack(anchor='w',padx=22,pady=(17,8))
        return win

    def fail(self,exc,win):
        text=str(exc)
        if isinstance(exc,sqlite3.IntegrityError):text='Código já cadastrado. Nos produtos, informe outro código; nos insumos, revise nome, tamanho e gramatura.'
        messagebox.showerror('Não foi possível salvar',text,parent=win)

    def material_dialog(self,m=None,parent=None,on_saved=None):
        win=self.modal('Editar insumo' if m else 'Novo insumo',700,610)
        if parent:
            win.transient(parent)
            def restore_grab(event):
                if event.widget is win and parent.winfo_exists():parent.grab_set()
            win.bind('<Destroy>',restore_grab)
        frame=tk.Frame(win,bg=SURFACE);frame.pack(fill='x',padx=16)
        frame.grid_columnconfigure(0,weight=1);frame.grid_columnconfigure(1,weight=1)
        name_var,size_var,gram_var=(tk.StringVar() for _ in range(3))
        name=field(frame,'NOME DO INSUMO',0,m['name'] if m else '',0,variable=name_var)
        unit=field(frame,'UNIDADE (un, m, g...)',0,m['unit'] if m else 'un',1)
        size=field(frame,'TAMANHO',2,m['size'] if m else '',0,variable=size_var)
        gram=field(frame,'GRAMATURA',2,m['grammage'] if m else '',1,variable=gram_var)
        qty=field(frame,'QUANTIDADE POR EMBALAGEM',4,fmt_qty(m['pack_qty']) if m else '1',0)
        price=field(frame,'PREÇO DA EMBALAGEM (R$)',4,f"{m['pack_cents']/100:.2f}".replace('.',',') if m else '',1)
        spec=field(frame,'OBSERVAÇÕES (OPCIONAL)',6,m['specification'] if m else '',0)
        code=field(frame,'CÓDIGO GERADO',6,m['code'] if m else '',1)
        variant_names=', '.join(v['name'] for v in self.store.variants(m['id'],active_only=True)) if m else ''
        variants=field(frame,'VARIAÇÕES POSSÍVEIS (SEPARADAS POR VÍRGULA)',8,variant_names,0,width=48)
        price_date=field(frame,'DATA DO PREÇO • DD/MM/AAAA',8,
                         br_date(m['price_date']) if m and m['price_date'] else ('' if m else date.today().strftime('%d/%m/%Y')),1)
        code.configure(state='readonly')
        def update_code(*_):
            if m:return
            try:computed=automatic_code(name_var.get(),size_var.get(),gram_var.get())
            except ValueError:computed=''
            code.configure(state='normal');code.delete(0,tk.END);code.insert(0,computed);code.configure(state='readonly')
        for variable in (name_var,size_var,gram_var):variable.trace_add('write',update_code)
        update_code()
        tk.Label(win,text='Código: 3 caracteres do nome + tamanho + gramatura. Ex.: OFFA4150.',
                 bg=SURFACE,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=26,pady=(10,0))
        tk.Label(win,text='Ex.: Dourado, Prata, Preto. Todas usam o mesmo preço do insumo.',
                 bg=SURFACE,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=26,pady=(3,0))
        def save():
            try:
                entered_date=price_date.get().strip()
                try:reference=parse_date(entered_date) if entered_date else ''
                except ValueError:raise ValueError('Informe a data do preço em DD/MM/AAAA.')
                saved_id=self.store.save_material(id=m['id'] if m else None,code=m['code'] if m else None,name=name.get(),
                  size=size.get(),grammage=gram.get(),specification=spec.get(),unit=unit.get(),
                  pack_qty=quantity(qty.get()),pack_cents=cents(price.get()),
                  variants=variants.get().split(','),price_date=reference)
                win.destroy()
                if on_saved:on_saved(saved_id)
                else:self.render()
            except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,win)
        button(win,'Salvar insumo',save).pack(side='right',padx=26,pady=25)

    def product_page(self):
        self.toolbar('Sugestão = custo dos insumos × multiplicador. Média = preço realizado por unidade.',
                     [('Novo produto',lambda:self.product_dialog(),True),
                      ('Editar',lambda:self.edit_product(),False),
                      ('Ativar / inativar',lambda:self.toggle_product(),False)])
        self.filter_bar()
        self.tree=grid(self.main,('Código','Produto','Tamanho','Gramatura','Custo','Sugerido','Tabela','Média vendida','Estado'),
                       (95,240,82,80,100,105,98,110,75))
        term=self.search.get().casefold()
        for p in self.store.products():
            if term not in (p['code']+' '+p['name']+' '+p['size']+' '+p['grammage']).casefold():continue
            cost,missing=self.store.product_cost(p['id']);suggested,_=self.store.suggested(p)
            status='Revisar' if cost is None else ('Ativo' if p['active'] else 'Inativo')
            self.tree.insert('',tk.END,iid=str(p['id']),values=(p['code'],p['name'],p['size'],p['grammage'],
                 money(round(cost)) if cost is not None else 'Revisar',money(suggested) if suggested is not None else 'Revisar',
                 money(p['table_cents']),money(self.store.mean_price(p['id'])),status))
        tk.Label(self.main,text='"Revisar" indica composição vazia ou insumo não encontrado na planilha original.',
                 bg=BG,fg=RED,font=('Segoe UI',9)).pack(anchor='w',padx=28,pady=(0,8))
        self.tree.bind('<Double-1>',lambda _:self.edit_product())

    def edit_product(self):
        id=self.selection(self.tree)
        if id:self.product_dialog(self.store.one('SELECT * FROM products WHERE id=?',(id,)))

    def toggle_product(self):
        id=self.selection(self.tree)
        if id:self.store.toggle_product(id);self.render()

    def product_dialog(self,p=None):
        win=self.modal('Editar produto' if p else 'Novo produto',850,735)
        body=tk.Frame(win,bg=SURFACE);body.pack(fill='x',padx=16)
        for i in range(2):body.grid_columnconfigure(i,weight=1)
        name_var,size_var,gram_var=(tk.StringVar() for _ in range(3))
        name=field(body,'NOME DO PRODUTO',0,p['name'] if p else '',0,variable=name_var)
        code=field(body,'CÓDIGO DO PRODUTO',0,p['code'] if p else '',1)
        size=field(body,'TAMANHO',2,p['size'] if p else '',0,variable=size_var)
        gram=field(body,'GRAMATURA',2,p['grammage'] if p else '',1,variable=gram_var)
        markup=field(body,'MULTIPLICADOR SOBRE O CUSTO',4,str(p['markup']).replace('.',',') if p else '1,8',0)
        table=field(body,'PREÇO DE TABELA (R$) • OPCIONAL',4,f"{p['table_cents']/100:.2f}".replace('.',',') if p and p['table_cents'] is not None else '',1)
        tk.Label(win,text='COMPOSIÇÃO • quantidade usada para produzir uma unidade',bg=SURFACE,fg=OLIVE,
                 font=('Segoe UI',10,'bold')).pack(anchor='w',padx=26,pady=(16,5))
        chooser=tk.Frame(win,bg=SURFACE);chooser.pack(fill='x',padx=20,pady=4)
        materials=[m for m in self.store.materials() if m['active']]
        mapping={f"{m['code']}  ·  {m['name']} ({m['size']} {m['grammage']})":m['code'] for m in materials}
        combo=ttk.Combobox(chooser,values=list(mapping),state='normal',width=38)
        combo.pack(side='left',padx=5,fill='x',expand=True)
        def search_materials(event=None):
            term=combo.get().strip().casefold()
            combo.configure(values=[label for label in mapping if term in label.casefold()])
        combo.bind('<KeyRelease>',search_materials)
        def refresh_materials(saved_id):
            mapping.clear()
            for material in self.store.materials():
                if not material['active']:continue
                label=f"{material['code']}  ·  {material['name']} ({material['size']} {material['grammage']})"
                mapping[label]=material['code']
                if material['id']==saved_id:combo.set(label)
            combo.configure(values=list(mapping))
            win.grab_set()
        button(chooser,'Novo insumo',lambda:self.material_dialog(parent=win,on_saved=refresh_materials),False).pack(side='left',padx=3)

        unit_qty=ttk.Entry(chooser,width=12);unit_qty.insert(0,'1');unit_qty.pack(side='left',padx=5)
        entries=[]
        table_frame=tk.Frame(win,bg=SURFACE);table_frame.pack(fill='both',expand=True,padx=20,pady=5)
        tree=ttk.Treeview(table_frame,columns=('Insumo','Qtd','Custo'),show='headings',height=6)
        for column,width in [('Insumo',420),('Qtd',90),('Custo',120)]:tree.heading(column,text=column);tree.column(column,width=width)
        tree.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(table_frame,orient='vertical',command=tree.yview);scroll.pack(side='right',fill='y');tree.configure(yscrollcommand=scroll.set)
        total_label=tk.Label(win,text='',bg=SURFACE,fg=RED,font=('Segoe UI',12,'bold'))
        total_label.pack(anchor='e',padx=25,pady=4)
        def redraw():
            tree.delete(*tree.get_children());running=0;missing=[]
            for i,(material_code,amount) in enumerate(entries):
                m=self.store.one('SELECT * FROM materials WHERE code=? COLLATE NOCASE',(material_code,))
                value=amount*m['pack_cents']/m['pack_qty'] if m else None
                if value is None:missing.append(material_code)
                else:running+=value
                tree.insert('',tk.END,iid=str(i),values=(f"{material_code} · {m['name']}" if m else material_code+' · NÃO ENCONTRADO',
                                                         fmt_qty(amount),money(round(value)) if value is not None else 'Revisar'))
            try:factor=float(markup.get().replace(',','.'))
            except ValueError:factor=1.8
            total_label.configure(text=('Corrija os insumos: '+', '.join(missing)) if missing else
                f'Custo: {money(round(running))}    •    Sugerido: {money(round(running*factor))}')
        def add():
            try:
                if combo.get() not in mapping:raise ValueError('Digite para buscar e selecione um insumo na lista.')
                entries.append((mapping[combo.get()],quantity(unit_qty.get())))
                redraw()
            except (ValueError,KeyError) as exc:self.fail(exc,win)
        button(chooser,'Adicionar',add,False).pack(side='left',padx=5)
        if p:entries.extend((r['material_code'],r['qty']) for r in self.store.recipe(p['id']))
        redraw()
        def remove():
            selected=tree.selection()
            if selected:entries.pop(int(selected[0]));redraw()
        buttons=tk.Frame(win,bg=SURFACE);buttons.pack(fill='x',padx=23,pady=(3,16))
        button(buttons,'Remover insumo selecionado',remove,False).pack(side='left')
        def save():
            try:
                factor=float(markup.get().strip().replace(',','.'))
                self.store.save_product(id=p['id'] if p else None,code=code.get(),name=name.get(),
                    size=size.get(),grammage=gram.get(),markup=factor,
                    table_cents=cents(table.get(),allow_empty=True),recipe=entries)
                win.destroy();self.render()
            except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,win)
        button(buttons,'Salvar produto',save).pack(side='right')

    def stock_page(self):
        self.toolbar('Saldos separados por variação e histórico de movimentações.',
                     [('Entrada',lambda:self.stock_dialog('entry'),True),
                      ('Retirada forçada',lambda:self.stock_dialog('manual_out'),False),
                      ('Ajustar saldo',lambda:self.stock_dialog('adjustment'),False),
                      ('Transferir',self.transfer_dialog,False)])
        tk.Label(self.main,text='O estoque começa em zero. Registre seu saldo inicial em Entrada ou Ajustar saldo; '
                 'pedidos antigos não são retirados novamente. Saldos negativos indicam falta de registro ou compra.',
                 bg=BG,fg=MUTED,wraplength=990,justify='left',font=('Segoe UI',9)).pack(anchor='w',padx=28,pady=(0,9))
        table_box=tk.Frame(self.main,bg=SURFACE)
        table_box.pack(fill='x',padx=26,pady=(0,13))
        columns=('Código','Insumo','Variação','Tamanho','Gramatura','Saldo','Unidade','Situação')
        self.stock_tree=ttk.Treeview(table_box,columns=columns,show='headings',height=9,selectmode='browse')
        for col,width in zip(columns,(115,210,170,92,88,95,76,88)):
            self.stock_tree.heading(col,text=col);self.stock_tree.column(col,width=width,minwidth=70)
        scroll=ttk.Scrollbar(table_box,orient='vertical',command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=scroll.set)
        self.stock_tree.pack(side='left',fill='x',expand=True);scroll.pack(side='right',fill='y')
        self.stock_tree.tag_configure('deficit',foreground=RED_DARK)
        self.stock_balances={};self.stock_rows={}
        for m in self.store.stock():
            key=f"{m['id']}:{m['variant_id'] or 0}"
            self.stock_balances[key]=m['balance'];self.stock_rows[key]=m
            status=('Negativo' if m['balance']<0 else 'Inativa' if not m['variant_active']
                    else 'Disponível' if m['balance']>0 else 'Zerado')
            self.stock_tree.insert('',tk.END,iid=key,tags=('deficit',) if m['balance']<0 else (),
                values=(m['code'],m['name'],m['variant_name'],m['size'],m['grammage'],
                        fmt_qty(m['balance']),m['unit'],status))
        tk.Label(self.main,text='Histórico do insumo selecionado',bg=BG,fg=OLIVE,
                 font=('Segoe UI',14,'bold')).pack(anchor='w',padx=26,pady=(0,3))
        self.stock_history_tree=grid(self.main,('Data','Movimento','Pedido','Quantidade','Saldo após','Motivo'),
                                     (100,145,100,115,105,340))
        self.stock_tree.bind('<<TreeviewSelect>>',lambda _:self.show_stock_history())
        if self.stock_tree.get_children():self.stock_tree.selection_set(self.stock_tree.get_children()[0]);self.show_stock_history()

    def show_stock_history(self):
        if not self.stock_tree.selection():return
        key=self.stock_tree.selection()[0]
        material=self.stock_rows[key]
        balance=self.stock_balances[key]
        self.stock_history_tree.delete(*self.stock_history_tree.get_children())
        names={'entry':'Entrada','manual_out':'Retirada forçada','adjustment':'Ajuste de saldo',
               'order_out':'Retirada por pedido','order_reversal':'Estorno de pedido',
               'transfer_out':'Transferência (saída)','transfer_in':'Transferência (entrada)'}
        for movement in self.store.stock_history(material['id'],variant_id=material['variant_id']):
            self.stock_history_tree.insert('',tk.END,values=(br_date(movement['effective_date']),
                names.get(movement['kind'],movement['kind']),movement['order_number'] or '—',
                ('+' if movement['delta']>0 else '')+fmt_qty(movement['delta']),fmt_qty(balance),movement['notes']))
            balance-=movement['delta']

    def stock_dialog(self,action):
        selection=self.stock_tree.selection()
        if not selection:
            messagebox.showinfo('Selecione um insumo','Selecione um insumo e uma variação da lista.',parent=self.root)
            return
        key=selection[0];m=self.stock_rows[key]
        title={'entry':'Entrada de estoque','manual_out':'Retirada forçada',
               'adjustment':'Corrigir saldo'}[action]
        win=self.modal(title,600,330)
        tk.Label(win,text=f"{m['code']} • {m['name']} • {m['variant_name']}  |  Saldo: {fmt_qty(self.stock_balances[key])} {m['unit']}",
                 bg=SURFACE,fg=OLIVE,font=('Segoe UI',11)).pack(anchor='w',padx=25,pady=(4,5))
        body=tk.Frame(win,bg=SURFACE);body.pack(fill='x',padx=16)
        label='SALDO FINAL DESEJADO' if action=='adjustment' else 'QUANTIDADE A '+('ENTRAR' if action=='entry' else 'RETIRAR')
        amount=field(body,label,0,fmt_qty(self.stock_balances[key]) if action=='adjustment' else '1')
        reason=field(body,'MOTIVO (OBRIGATÓRIO)',2,'')
        tk.Label(win,text='A retirada forçada pode deixar o saldo negativo. Cada alteração fica no histórico.',
                 bg=SURFACE,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=25,pady=(9,0))
        def save():
            try:
                value=float(amount.get().strip().replace(',','.')) if action=='adjustment' else quantity(amount.get())
                if not math.isfinite(value):raise ValueError('Informe um saldo válido.')
                self.store.adjust_stock(m['id'],action,value,reason.get(),variant_id=m['variant_id'])
                win.destroy();self.render();self.stock_tree.selection_set(key);self.stock_tree.see(key);self.show_stock_history()
            except ValueError as exc:self.fail(exc,win)
        button(win,'Registrar movimentação',save).pack(side='right',padx=25,pady=19)

    def transfer_dialog(self):
        selection=self.stock_tree.selection()
        if not selection:
            messagebox.showinfo('Selecione uma origem','Selecione o insumo e a variação de origem.',parent=self.root)
            return
        key=selection[0];source=self.stock_rows[key]
        options=[v for v in self.store.variants(source['id'],active_only=True)
                 if v['id']!=source['variant_id']]
        if not options:
            messagebox.showinfo('Sem destino','Cadastre outra variação ativa neste insumo para transferir.',parent=self.root)
            return
        win=self.modal('Transferir entre variações',630,360)
        tk.Label(win,text=f"Origem: {source['name']} • {source['variant_name']} | Saldo: {fmt_qty(source['balance'])} {source['unit']}",
                 bg=SURFACE,fg=OLIVE,font=('Segoe UI',11)).pack(anchor='w',padx=25,pady=(4,10))
        body=tk.Frame(win,bg=SURFACE);body.pack(fill='x',padx=20)
        tk.Label(body,text='VARIAÇÃO DE DESTINO',bg=SURFACE,fg=OLIVE,
                 font=('Segoe UI',9,'bold')).pack(anchor='w')
        target=ttk.Combobox(body,values=[v['name'] for v in options],state='readonly',width=35)
        target.pack(anchor='w',fill='x',pady=(3,8))
        form=tk.Frame(win,bg=SURFACE);form.pack(fill='x',padx=15)
        amount=field(form,'QUANTIDADE A TRANSFERIR',0,'1')
        reason=field(form,'MOTIVO',2,'Distribuição por variação')
        def save():
            try:
                if not target.get():raise ValueError('Selecione a variação de destino.')
                destination=next(v['id'] for v in options if v['name']==target.get())
                self.store.transfer_stock(source['id'],source['variant_id'],destination,
                                          quantity(amount.get()),reason.get())
                win.destroy();self.render()
                if key in self.stock_rows:
                    self.stock_tree.selection_set(key);self.stock_tree.see(key);self.show_stock_history()
            except ValueError as exc:self.fail(exc,win)
        button(win,'Transferir',save).pack(side='right',padx=25,pady=13)

    def calendar_page(self):
        today=date.today()
        month=self.calendar_month
        by_day={}
        for order in self.store.orders():
            if order['due_date'] and order['due_date'].startswith(month.strftime('%Y-%m-')):
                day=int(order['due_date'][8:])
                by_day.setdefault(day,[]).append(order)
        controls=tk.Frame(self.main,bg=BG)
        controls.pack(fill='x',padx=26,pady=(0,10))
        def move(delta):
            index=month.year*12+month.month-1+delta
            self.calendar_month=date(index//12,index%12+1,1)
            self.calendar_selected=self.calendar_month
            self.render()
        button(controls,'‹ Mês anterior',lambda:move(-1),False).pack(side='left')
        tk.Label(controls,text=f'{MONTHS[month.month]} de {month.year}',bg=BG,fg=OLIVE,
                 font=('Segoe UI',16,'bold')).pack(side='left',padx=24)
        button(controls,'Próximo mês ›',lambda:move(1),False).pack(side='left')
        button(controls,'Hoje',lambda:self.calendar_today(),False).pack(side='right')
        calendar_box=tk.Frame(self.main,bg=CREAM)
        calendar_box.pack(fill='x',padx=26)
        for column,title in enumerate(('Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo')):
            calendar_box.grid_columnconfigure(column,weight=1,uniform='days')
            tk.Label(calendar_box,text=title,bg=OLIVE,fg='white',font=('Segoe UI',9,'bold'),
                     pady=5).grid(row=0,column=column,sticky='ew',padx=1,pady=1)
        for row,week in enumerate(calendar.monthcalendar(month.year,month.month),start=1):
            for column,day in enumerate(week):
                events=by_day.get(day,[])
                selected=(month.year,month.month,day)==(
                    self.calendar_selected.year,self.calendar_selected.month,self.calendar_selected.day)
                bg=CREAM if not day else ('#F2D2C0' if selected else SURFACE)
                entries='\n'.join(f"{o['number']} · {o['customer'][:11]}" for o in events[:2])
                if len(events)>2:entries+=f'\n+{len(events)-2} pedidos'
                label=(str(day)+'\n'+entries) if day else ''
                def choose(value=day):
                    self.calendar_selected=date(month.year,month.month,value)
                    self.render()
                tk.Button(calendar_box,text=label,command=choose if day else None,state='normal' if day else 'disabled',
                          anchor='nw',justify='left',wraplength=110,relief='flat',bd=0,cursor='hand2' if day else 'arrow',
                          bg=bg,fg=RED if events else OLIVE,activebackground='#F2D2C0',
                          font=('Segoe UI',9,'bold' if events else 'normal'),height=4,
                          padx=7).grid(row=row,column=column,sticky='nsew',padx=1,pady=1)
        selected=self.calendar_selected
        tk.Label(self.main,text='Entregas em '+selected.strftime('%d/%m/%Y'),bg=BG,fg=OLIVE,
                 font=('Segoe UI',12,'bold')).pack(anchor='w',padx=26,pady=(13,0))
        self.calendar_tree=grid(self.main,('Pedido','Cliente','Pagamento','Produção','Total','Restante'),
                                (105,230,115,145,110,110))
        for o in by_day.get(selected.day,[]) if selected.year==month.year and selected.month==month.month else []:
            self.calendar_tree.insert('',tk.END,iid=str(o['id']),values=(o['number'],o['customer'],
               o['payment'],o['production'],money(o['total_cents']) if not o['unpriced'] else 'A definir',
               money(o['remaining_cents'])))
        def open_order(_=None):
            if self.calendar_tree.selection():
                self.order_dialog(self.store.order(int(self.calendar_tree.selection()[0])))
        self.calendar_tree.bind('<Double-1>',open_order)

    def calendar_today(self):
        self.calendar_selected=date.today()
        self.calendar_month=self.calendar_selected.replace(day=1)
        self.render()

    def order_page(self):
        self.toolbar('Gerencie pedidos e comprovantes.',
                     [('Novo pedido',lambda:self.order_dialog(),True),('Editar',lambda:self.edit_order(),False),
                      ('Gerar PDF',lambda:self.pdf_selected(),False),
                      ('Excluir pedido',self.delete_selected_order,False)])
        panel=tk.Frame(self.main,bg=CREAM)
        panel.pack(fill='x',padx=26,pady=(3,8))
        specs=[('number','Nº'),('customer','Cliente'),('items','Itens'),('created','Criado'),('due','Entrega'),
               ('payment','Pagamento'),('production','Produção'),('min_total','Total mínimo (R$)'),
               ('max_total','Total máximo (R$)'),('min_remaining','Restante mínimo (R$)'),
               ('max_remaining','Restante máximo (R$)')]
        orders=self.store.orders()
        for index,(key,title) in enumerate(specs):
            row,col=divmod(index,5)
            panel.grid_columnconfigure(col,weight=1)
            box=tk.Frame(panel,bg=CREAM)
            box.grid(row=row,column=col,sticky='ew',padx=7,pady=(5,7))
            tk.Label(box,text=title,bg=CREAM,fg=OLIVE,font=('Segoe UI',9,'bold')).pack(anchor='w')
            if key not in self.order_filters:
                self.order_filters[key]=tk.StringVar(value='Todos' if key in ('payment','production') else '')
                self.order_filters[key].trace_add('write',lambda *_:self.update_order_results())
            if key in ('payment','production'):
                choices=['Todos']+sorted({o[key] for o in orders if o[key]})
                input_widget=ttk.Combobox(box,textvariable=self.order_filters[key],values=choices,state='readonly',width=14)
            else:
                input_widget=ttk.Entry(box,textvariable=self.order_filters[key],width=17)
            input_widget.pack(fill='x')
        button(panel,'Limpar filtros',self.clear_order_filters,False).grid(row=2,column=4,sticky='e',padx=8,pady=5)
        self.filter_count=tk.Label(self.main,text='',bg=BG,fg=MUTED,font=('Segoe UI',9))
        self.filter_count.pack(anchor='w',padx=28)
        self.tree=grid(self.main,('Nº','Cliente','Itens','Criado','Entrega','Pagamento','Produção','Total','Restante'),
                       (90,145,245,92,100,105,115,95,95))
        for column in self.tree['columns']:self.tree.column(column,stretch=False)
        self.update_order_results()
        self.tree.bind('<Double-1>',lambda _:self.edit_order())

    def delete_selected_order(self):
        id=self.selection(self.tree)
        if id is None:return
        order=self.store.order(id)
        if order is None:
            messagebox.showerror('Pedido não encontrado','Atualize a lista de pedidos.',parent=self.root)
            return
        if not messagebox.askyesno('Excluir pedido',
                f"Excluir definitivamente o pedido {order['number']} de {order['customer']}?\n\n"
                'A retirada automática dos insumos será estornada no estoque. '
                'O histórico das movimentações será preservado.',parent=self.root):
            return
        try:
            self.store.delete_order(id)
            self.render()
        except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,self.root)

    def clear_order_filters(self):
        for key,var in self.order_filters.items():var.set('Todos' if key in ('payment','production') else '')
        self.update_order_results()

    def update_order_results(self):
        if self.page!='Pedidos' or not hasattr(self,'tree') or not hasattr(self,'filter_count'):
            return
        try:
            values={key:(cents(var.get(),allow_empty=True) if key in ('min_total','max_total','min_remaining','max_remaining')
                         else '' if var.get()=='Todos' else var.get()) for key,var in self.order_filters.items()}
        except ValueError:
            self.filter_count.configure(text='Digite um valor válido nos filtros de total.')
            return
        orders=filter_orders(self.store.orders(),values)
        self.tree.delete(*self.tree.get_children())
        for o in orders:
            self.tree.insert('',tk.END,iid=str(o['id']),values=(o['number'],o['customer'],o['descriptions'],
                br_date(o['created_date']),br_date(o['due_date']),o['payment'],o['production'],
                money(o['total_cents']) if not o['unpriced'] else 'A definir',
                money(o['remaining_cents'])))
        self.filter_count.configure(text=f'{len(orders)} pedido(s) exibido(s)')

    def report_page(self):
        self.toolbar('Resumo por mês de cadastro do pedido. Selecione Total para ver todo o histórico.',
                     [('Exportar PDF',self.export_report,True)])
        period=tk.Frame(self.main,bg=SURFACE)
        period.pack(fill='x',padx=26,pady=(4,15))
        for col in range(3):period.grid_columnconfigure(col,weight=1)
        tk.Label(period,text='MÊS',bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold')).grid(row=0,column=0,sticky='w',padx=10,pady=(12,3))
        self.month_combo=ttk.Combobox(period,values=MONTHS,state='readonly',width=25)
        self.month_combo.grid(row=1,column=0,sticky='ew',padx=10)
        self.month_combo.set(MONTHS[self.report_month] if self.report_month else 'Total')
        tk.Label(period,text='ANO',bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold')).grid(row=0,column=1,sticky='w',padx=10,pady=(12,3))
        years=sorted({date.today().year-1,date.today().year,date.today().year+1,self.report_year}|
                     {int(o['created_date'][:4]) for o in self.store.orders() if o['created_date']},reverse=True)
        self.year_combo=ttk.Combobox(period,values=years,state='readonly',width=16)
        self.year_combo.grid(row=1,column=1,sticky='ew',padx=10)
        self.year_combo.set(str(self.report_year))
        button(period,'Aplicar',self.apply_report,False).grid(row=1,column=2,padx=13,sticky='w')
        self.month_combo.bind('<<ComboboxSelected>>',lambda _:self.month_changed())
        self.year_combo.bind('<<ComboboxSelected>>',lambda _:self.apply_report())
        self.month_changed(refresh=False)
        cards=tk.Frame(self.main,bg=BG);cards.pack(fill='x',padx=22,pady=(0,16))
        self.report_labels=[]
        for i,title in enumerate(('PEDIDOS','EM ABERTO','TOTAL COM PREÇO','TICKET MÉDIO')):
            card=tk.Frame(cards,bg=CREAM)
            card.grid(row=0,column=i,padx=5,sticky='nsew')
            cards.grid_columnconfigure(i,weight=1)
            tk.Label(card,text=title,bg=CREAM,fg=OLIVE,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=13,pady=(12,5))
            value=tk.Label(card,text='',bg=CREAM,fg=RED,font=('Segoe UI',18,'bold'))
            value.pack(anchor='w',padx=13,pady=(0,12));self.report_labels.append(value)
        self.report_summary=tk.Label(self.main,bg=BG,fg=MUTED,font=('Segoe UI',9),wraplength=850,justify='left')
        self.report_summary.pack(anchor='w',padx=28,pady=(0,12))
        tk.Label(self.main,text='Itens vendidos por valor registrado',bg=BG,fg=OLIVE,
                 font=('Segoe UI',14,'bold')).pack(anchor='w',padx=26,pady=(0,4))
        self.report_tree=grid(self.main,('Produto ou item avulso','Quantidade','Valor registrado'),(490,120,180))
        self.apply_report()

    def month_changed(self,refresh=True):
        self.year_combo.configure(state='disabled' if self.month_combo.get()=='Total' else 'readonly')
        if refresh:self.apply_report()

    def apply_report(self):
        try:
            month=MONTHS.index(self.month_combo.get())
            year=int(self.year_combo.get())
            data=self.store.report_data(month or None,year)
        except ValueError as exc:
            self.fail(exc,self.root)
            return None
        self.report_month,self.report_year=month,year
        self.report_data_current=data
        for label,value in zip(self.report_labels,(str(data['count']),str(data['open']),
                                money(data['revenue']),money(data['average_ticket']))):
            label.configure(text=value)
        payments=', '.join(f'{status}: {count}' for status,count in data['payment']) or 'Sem pedidos'
        self.report_summary.configure(text=f'Pagamento: {payments}.  '
           f'Pedidos sem valor definido: {data["unknown"]} (fora dos valores e itens vendidos). '
           +('Pedidos antigos sem data de cadastro aparecem apenas em Total.' if month else ''))
        self.report_tree.delete(*self.report_tree.get_children())
        for index,row in enumerate(data['products']):
            self.report_tree.insert('',tk.END,iid=str(index),values=(row['name'],fmt_qty(row['quantity']),
                                                             money(round(row['total_cents']))))
        return data

    def export_report(self):
        data=self.apply_report()
        if data is None:return
        suffix=f'{self.report_year}_{self.report_month:02d}' if self.report_month else 'Total'
        target=filedialog.asksaveasfilename(parent=self.root,defaultextension='.pdf',
                  filetypes=[('Arquivo PDF','*.pdf')],initialfile=f'Relatorio_Papeis_de_Marte_{suffix}.pdf',
                  title='Salvar relatório de pedidos')
        if target:
            try:
                export_report_pdf(data,target)
                messagebox.showinfo('Relatório exportado',f'PDF salvo em:\n{target}',parent=self.root)
            except Exception as exc:self.fail(exc,self.root)

    def edit_order(self):
        id=self.selection(self.tree)
        if id:self.order_dialog(self.store.order(id))

    def pdf_selected(self):
        id=self.selection(self.tree)
        if id:self.export(id)

    def export(self,id,parent=None):
        order=self.store.order(id)
        target=filedialog.asksaveasfilename(parent=parent or self.root,defaultextension='.pdf',
                                            filetypes=[('Arquivo PDF','*.pdf')],initialfile=order['number']+'.pdf',
                                            title='Salvar comprovante do pedido')
        if target:
            try:
                export_order_pdf(self.store,id,target)
                messagebox.showinfo('Pedido gerado',f'PDF salvo em:\n{target}',parent=parent or self.root)
            except Exception as exc:self.fail(exc,parent or self.root)

    def ask_variants(self,parent,product):
        required=self.store.variant_requirements(product['id'])
        if not required:return {}
        dialog=tk.Toplevel(parent)
        dialog.title('Escolha as variações dos insumos')
        dialog.configure(bg=SURFACE)
        dialog.geometry(f'560x{min(500,170+72*len(required))}')
        dialog.transient(parent);dialog.grab_set()
        tk.Label(dialog,text=product['name'],bg=SURFACE,fg=OLIVE,
                 font=('Segoe UI',15,'bold')).pack(anchor='w',padx=23,pady=(18,4))
        tk.Label(dialog,text='Escolha uma variação para cada insumo. Todas têm o mesmo custo.',
                 bg=SURFACE,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=23,pady=(0,11))
        choices=[]
        for material,options in required:
            row=tk.Frame(dialog,bg=SURFACE);row.pack(fill='x',padx=23,pady=5)
            tk.Label(row,text=f"{material['name']} ({material['code']})",bg=SURFACE,fg=OLIVE,
                     font=('Segoe UI',10),width=25,anchor='w').pack(side='left')
            combo=ttk.Combobox(row,values=[v['name'] for v in options],state='readonly',width=24)
            combo.pack(side='left',fill='x',expand=True)
            choices.append((material,options,combo))
        result=[None]
        def confirm():
            if any(not combo.get() for _,_,combo in choices):
                messagebox.showerror('Falta uma variação','Escolha a variação de cada insumo.',parent=dialog)
                return
            result[0]={m['id']:next(v['id'] for v in options if v['name']==combo.get())
                       for m,options,combo in choices}
            dialog.destroy()
        actions=tk.Frame(dialog,bg=SURFACE);actions.pack(fill='x',padx=22,pady=17)
        button(actions,'Cancelar',dialog.destroy,False).pack(side='left')
        button(actions,'Confirmar variações',confirm).pack(side='right')
        dialog.protocol('WM_DELETE_WINDOW',dialog.destroy)
        parent.wait_window(dialog)
        parent.grab_set()
        return result[0]

    def order_dialog(self,o=None):
        win=self.modal(f"Pedido {o['number']}" if o else 'Novo pedido',900,710)
        win.minsize(680,420)
        width=max(680,min(900,win.winfo_screenwidth()-80))
        height=max(420,min(710,win.winfo_screenheight()-100))
        win.geometry(f'{width}x{height}')
        foot=tk.Frame(win,bg=SURFACE)
        foot.pack(side='bottom',fill='x',padx=23,pady=(7,13))
        area=tk.Frame(win,bg=SURFACE)
        area.pack(fill='both',expand=True)
        canvas=tk.Canvas(area,bg=SURFACE,highlightthickness=0)
        scrollbar=ttk.Scrollbar(area,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y')
        canvas.pack(side='left',fill='both',expand=True)
        content=tk.Frame(canvas,bg=SURFACE)
        content_window=canvas.create_window((0,0),window=content,anchor='nw')
        content.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda event:canvas.itemconfigure(content_window,width=event.width))
        body=tk.Frame(content,bg=SURFACE);body.pack(fill='x',padx=15)
        for i in range(2):body.grid_columnconfigure(i,weight=1)
        customer=field(body,'CLIENTE',0,o['customer'] if o else '',0)
        tk.Label(body,text='ENTREGA • DD/MM/AAAA',bg=SURFACE,fg=OLIVE,
                 font=('Segoe UI',9,'bold')).grid(row=0,column=1,sticky='w',padx=10,pady=(12,3))
        due_box=tk.Frame(body,bg=SURFACE)
        due_box.grid(row=1,column=1,sticky='ew',padx=10,pady=(0,3))
        due=ttk.Entry(due_box)
        due.pack(side='left',fill='x',expand=True)
        if o and o['due_date']:due.insert(0,br_date(o['due_date']))
        button(due_box,'▦',lambda:pick_date(win,due),False).pack(side='left',padx=(5,0))
        tk.Label(body,text='PAGAMENTO',bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold')).grid(row=2,column=0,sticky='w',padx=10,pady=(12,3))
        payment=ttk.Combobox(body,values=['Pendente','Parcial','Pago','Presente'],state='readonly')
        payment.grid(row=3,column=0,sticky='ew',padx=10);payment.set(o['payment'] if o else 'Pendente')
        tk.Label(body,text='PRODUÇÃO',bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold')).grid(row=2,column=1,sticky='w',padx=10,pady=(12,3))
        production=ttk.Combobox(body,values=['Novo','Criando arte','Aguardando aprovação','Em produção','Pronto','Entregue'],state='normal')
        production.grid(row=3,column=1,sticky='ew',padx=10);production.set(o['production'] if o else 'Novo')
        partial_title=tk.Label(body,text='VALOR RECEBIDO (R$)',bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold'))
        partial_title.grid(row=4,column=0,sticky='w',padx=10,pady=(12,3))
        paid_var=tk.StringVar(value=f'{o["paid_cents"]/100:.2f}'.replace('.',',') if o and o['payment']=='Parcial' else '')
        paid_entry=ttk.Entry(body,textvariable=paid_var)
        paid_entry.grid(row=5,column=0,sticky='ew',padx=10)
        remaining_title=tk.Label(body,text='PAGAMENTO RESTANTE',bg=SURFACE,fg=OLIVE,font=('Segoe UI',9,'bold'))
        remaining_title.grid(row=4,column=1,sticky='w',padx=10,pady=(12,3))
        remaining_label=tk.Label(body,text='—',bg=SURFACE,fg=RED,font=('Segoe UI',11,'bold'))
        remaining_label.grid(row=5,column=1,sticky='w',padx=10)
        def toggle_partial(_=None):
            if payment.get()=='Parcial':
                for widget in (partial_title,paid_entry,remaining_title,remaining_label):widget.grid()
                redraw()
            else:
                for widget in (partial_title,paid_entry,remaining_title,remaining_label):widget.grid_remove()
        payment.bind('<<ComboboxSelected>>',toggle_partial)
        tk.Label(content,text='ITENS DO PEDIDO',bg=SURFACE,fg=OLIVE,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=25,pady=(18,5))
        row=tk.Frame(content,bg=SURFACE);row.pack(fill='x',padx=20)
        products=[p for p in self.store.products() if p['active']]
        product_map={f"{p['code']} · {p['name']}":p for p in products}
        selector=ttk.Combobox(row,values=['Personalizado / avulso']+list(product_map),state='readonly',width=35)
        selector.pack(side='left',padx=4,fill='x',expand=True);selector.set('Personalizado / avulso')
        desc=ttk.Entry(row,width=29);desc.pack(side='left',padx=4,fill='x',expand=True)
        amount=ttk.Entry(row,width=7);amount.insert(0,'1');amount.pack(side='left',padx=4)
        price=ttk.Entry(row,width=12);price.pack(side='left',padx=4)
        selected_variants={}
        def pick(_=None):
            nonlocal selected_variants
            p=product_map.get(selector.get())
            if p:
                selections=self.ask_variants(win,p)
                if selections is None:
                    selector.set('Personalizado / avulso')
                    desc.delete(0,tk.END);price.delete(0,tk.END);selected_variants={}
                    return
                selected_variants=selections
                desc.delete(0,tk.END);desc.insert(0,p['name'])
                suggested,_=self.store.suggested(p)
                val=p['table_cents'] if p['table_cents'] is not None else suggested
                price.delete(0,tk.END)
                if val is not None:price.insert(0,f'{val/100:.2f}'.replace('.',','))
            else:selected_variants={}
        selector.bind('<<ComboboxSelected>>',pick)
        tk.Label(content,text='Produto / tipo de item                              Descrição                                 Qtd              Preço (R$)',
                 bg=SURFACE,fg=MUTED,font=('Segoe UI',8)).pack(anchor='w',padx=26)
        items=[dict(product_id=i['product_id'],description=i['description'],qty=i['qty'],
                    unit_cents=i['unit_cents'],variants=i['variants'])
               for i in self.store.items(o['id'])] if o else []
        tree=ttk.Treeview(content,columns=('Descrição','Variações','Qtd','Valor un.','Total'),show='headings',height=5)
        for col,w in [('Descrição',295),('Variações',255),('Qtd',65),('Valor un.',100),('Total',100)]:
            tree.heading(col,text=col);tree.column(col,width=w)
        tree.pack(fill='both',expand=True,padx=25,pady=(8,3))
        total=tk.Label(content,text='',bg=SURFACE,fg=RED,font=('Segoe UI',13,'bold'))
        total.pack(anchor='e',padx=29,pady=3)
        def redraw():
            tree.delete(*tree.get_children());sum_cents=0;unknown=False
            for i,item in enumerate(items):
                part=round(item['qty']*item['unit_cents']) if item['unit_cents'] is not None else None
                if part is None:unknown=True
                else:sum_cents+=part
                variation_text=', '.join(self.store.variant_labels(item.get('variants'))) or '—'
                tree.insert('',tk.END,iid=str(i),values=(item['description'],variation_text,
                    fmt_qty(item['qty']),money(item['unit_cents']),money(part)))
            total.configure(text='TOTAL: '+('A definir' if unknown else money(sum_cents)))
            if payment.get()=='Parcial':
                try:
                    received=cents(paid_var.get())
                    remaining_label.config(text=money(max(0,sum_cents-received)) if not unknown else 'A definir')
                except ValueError:
                    remaining_label.config(text='Informe o valor recebido')
        paid_var.trace_add('write',lambda *_:redraw())
        redraw()
        toggle_partial()
        actions=tk.Frame(content,bg=SURFACE);actions.pack(fill='x',padx=22,pady=5)
        def add():
            nonlocal selected_variants
            try:
                if not desc.get().strip():raise ValueError('Informe a descrição do item.')
                p=product_map.get(selector.get())
                if p and self.store.variant_requirements(p['id']) and not selected_variants:
                    raise ValueError('Escolha as variações dos insumos antes de adicionar o produto.')
                items.append(dict(product_id=p['id'] if p else None,description=desc.get().strip(),
                                  qty=quantity(amount.get()),unit_cents=cents(price.get()),
                                  variants=dict(selected_variants) if p else {}))
                redraw();selector.set('Personalizado / avulso');desc.delete(0,tk.END);price.delete(0,tk.END)
                selected_variants={};amount.delete(0,tk.END);amount.insert(0,'1')
            except ValueError as exc:self.fail(exc,win)
        button(actions,'Adicionar item',add,False).pack(side='left',padx=4)
        def change_variants():
            if not tree.selection():
                messagebox.showinfo('Selecione um item','Selecione um item do pedido.',parent=win)
                return
            item=items[int(tree.selection()[0])]
            if not item.get('product_id'):
                messagebox.showinfo('Item avulso','Esse item não usa a composição de um produto cadastrado.',parent=win)
                return
            product=self.store.one('SELECT * FROM products WHERE id=?',(item['product_id'],))
            if not self.store.variant_requirements(product['id']):
                messagebox.showinfo('Sem variações','A composição deste produto não tem variações cadastradas.',parent=win)
                return
            updated=self.ask_variants(win,product)
            if updated is not None:
                item['variants']=updated
                redraw()
        button(actions,'Trocar variações',change_variants,False).pack(side='left',padx=4)
        def remove():
            if tree.selection():items.pop(int(tree.selection()[0]));redraw()
        button(actions,'Remover item',remove,False).pack(side='left',padx=4)
        tk.Label(content,text='OBSERVAÇÕES / PERSONALIZAÇÃO',bg=SURFACE,fg=OLIVE,
                 font=('Segoe UI',9,'bold')).pack(anchor='w',padx=26,pady=(8,2))
        notes=tk.Text(content,height=3,font=('Segoe UI',10),wrap='word',bd=1,relief='solid',highlightthickness=0)
        notes.pack(fill='x',padx=26)
        if o:notes.insert('1.0',o['notes'])
        if o:button(foot,'Gerar PDF',lambda:self.export(o['id'],win),False).pack(side='left')
        def save():
            try:
                id=self.store.save_order(id=o['id'] if o else None,customer=customer.get(),
                  due_date=parse_date(due.get()),payment=payment.get(),production=production.get().strip() or 'Novo',
                  notes=notes.get('1.0',tk.END),items=items,
                  paid_cents=cents(paid_var.get()) if payment.get()=='Parcial' else 0)
                win.destroy();self.render()
                if not o:messagebox.showinfo('Pedido salvo',f'Pedido {self.store.order(id)["number"]} registrado.',parent=self.root)
            except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,win)
        button(foot,'Salvar pedido',save).pack(side='right')

    def backup(self):
        destination=filedialog.asksaveasfilename(parent=self.root,defaultextension='.db',
                        filetypes=[('Banco de dados','*.db')],initialfile='marte_backup_'+date.today().isoformat()+'.db')
        if destination:
            try:
                self.store.backup(destination)
                messagebox.showinfo('Cópia salva',f'Cópia dos dados salva em:\n{destination}',parent=self.root)
            except Exception as exc:self.fail(exc,self.root)


if __name__=='__main__':
    config=read_config(asset('update_config.json'))
    if launch_cached(config,data_directory()):
        raise SystemExit(0)
    root=tk.Tk()
    root.iconphoto(True,tk.PhotoImage(file=str(asset('logo.png'))))
    ERP(root)
    root.mainloop()
