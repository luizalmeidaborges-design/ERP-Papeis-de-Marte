"""Telas de catálogo, clientes e revisão de CSV."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import math
from pathlib import Path
from datetime import date
from visual_theme import BG,SURFACE,CREAM,RED,OLIVE,MUTED,ScrollArea,StripedTreeview
from catalog_core import positive_int, rounded


class CatalogUI:
    def collapsible_filters(self,parent=None):
        parent=parent or self.main
        host=tk.Frame(parent,bg=BG);host.pack(fill='x',padx=26,pady=4)
        box=tk.Frame(host,bg=BG)
        def toggle():
            if box.winfo_manager():box.pack_forget();btn.configure(text='▸ Mostrar filtros')
            else:box.pack(fill='x',pady=5);btn.configure(text='▾ Recolher filtros')
        btn=ttk.Button(host,text='▸ Mostrar filtros',command=toggle);btn.pack(anchor='w')
        return box

    def customer_dialog(self,c=None,parent=None,name=''):
        from app import field,button
        from core import br_date,parse_date
        win=self.modal('Editar cliente' if c else 'Cadastrar cliente',650,550)
        if parent:win.transient(parent)
        form=tk.Frame(win,bg=SURFACE);form.pack(fill='x',padx=18)
        form.columnconfigure(0,weight=1);form.columnconfigure(1,weight=1)
        fields={}
        for key,label,row,col,value in [('name','NOME *',0,0,c['name'] if c else name),('phone','TELEFONE',0,1,c['phone'] if c else ''),
          ('email','E-MAIL',2,0,c['email'] if c else ''),('birthday','NASCIMENTO • DD/MM/AAAA',2,1,br_date(c['birthday']) if c else ''),
          ('address','ENDEREÇO COMPLETO',4,0,c['address'] if c else '')]:fields[key]=field(form,label,row,value,col)
        fields['address'].grid_configure(columnspan=2)
        result=[]
        def save():
            try:
                data={k:v.get() for k,v in fields.items()}
                data['birthday']=parse_date(data['birthday']) if data['birthday'].strip() else ''
                result.append(self.store.save_customer(id=c['id'] if c else None,**data));win.destroy()
            except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,win)
        button(win,'Salvar cliente',save).pack(side='bottom',anchor='e',padx=25,pady=20)
        win.wait_window()
        if parent and parent.winfo_exists():parent.grab_set()
        return result[0] if result else None

    def customer_page(self):
        from app import grid,button
        from core import br_date
        def edit(new=False):
            selected=None if new else self.selection(self.tree)
            if new or selected:
                if self.customer_dialog(self.store.one('SELECT * FROM customers WHERE id=?',(selected,)) if selected else None):self.render()
        self.toolbar('Cadastro de clientes.',[('Novo cliente',lambda:edit(True),True),('Editar',edit,False)])
        filters=self.collapsible_filters();search=tk.StringVar()
        ttk.Label(filters,text='Nome, telefone ou e-mail').pack(side='left')
        ttk.Entry(filters,textvariable=search,width=45).pack(side='left',padx=8)
        self.tree=grid(self.main,('Nome','Telefone','E-mail','Nascimento','Endereço'),(220,145,230,120,280))
        def fill(*_):
            self.tree.delete(*self.tree.get_children())
            for c in self.store.customers():
                if search.get().casefold() not in (c['name']+' '+c['phone']+' '+c['email']).casefold():continue
                self.tree.insert('', 'end',iid=str(c['id']),values=(c['name'],c['phone'],c['email'],br_date(c['birthday']),c['address']))
        search.trace_add('write',fill);fill();self.tree.bind('<Double-1>',lambda _:edit())

    def material_dialog(self,m=None,parent=None,on_saved=None):
        from app import field,button
        from core import automatic_code,fmt_qty,cents,quantity,br_date,parse_date
        win=self.modal('Editar insumo' if m else 'Novo insumo',850,790)
        if parent:win.transient(parent)
        foot=tk.Frame(win,bg=SURFACE);foot.pack(side='bottom',fill='x',padx=22,pady=12)
        area=ScrollArea(win,background=SURFACE,min_width=740,min_height=700);area.pack(fill='both',expand=True);content=area.content
        frame=tk.Frame(content,bg=SURFACE);frame.pack(fill='x',padx=18)
        for i in range(2):frame.columnconfigure(i,weight=1)
        name=field(frame,'NOME DO INSUMO',0,m['name'] if m else '')
        unit=field(frame,'UNIDADE (folha, un, m, g...)',0,m['unit'] if m else 'un',1)
        size=field(frame,'TAMANHO',2,m['size'] if m else '')
        gram=field(frame,'GRAMATURA',2,m['grammage'] if m else '',1)
        qty=field(frame,'QUANTIDADE POR EMBALAGEM / ROLO',4,fmt_qty(m['pack_qty']) if m else '1')
        price=field(frame,'VALOR DA EMBALAGEM (R$)',4,str(m['pack_cents']/100) if m else '',1)
        code=field(frame,'CÓDIGO',6,m['code'] if m else '')
        dt=field(frame,'DATA DO PREÇO • DD/MM/AAAA',6,br_date(m['price_date']) if m and m['price_date'] else date.today().strftime('%d/%m/%Y'),1)
        spec=field(frame,'OBSERVAÇÕES',8,m['specification'] if m else '')
        tk.Label(frame,text='CATEGORIA',bg=SURFACE,fg=OLIVE).grid(row=8,column=1,sticky='w',padx=10,pady=(12,3))
        category=ttk.Combobox(frame,values=('Produção','Embalagem'),state='readonly');category.grid(row=9,column=1,sticky='ew',padx=10)
        category.set(m['category'] if m else 'Produção')
        def autocode(_=None):
            if not m:
                code.delete(0,'end');code.insert(0,automatic_code(name.get(),size.get(),gram.get()))
        for w in (name,size,gram):w.bind('<KeyRelease>',autocode)
        tk.Label(content,text='OPÇÕES E VARIAÇÕES • adicione quantas linhas precisar\nEx.: Opção Wire-o 3/4, variação Dourado. Preço vazio usa o valor da embalagem acima.',bg=SURFACE,fg=OLIVE,justify='left').pack(anchor='w',padx=28,pady=12)
        row=tk.Frame(content,bg=SURFACE);row.pack(fill='x',padx=22)
        option=field(row,'OPÇÃO',0,'Cor',0,width=18);value=field(row,'VARIAÇÃO',0,'',1,width=20);vp=field(row,'VALOR EMBALAGEM (R$)',0,'',2,width=18)
        tree=StripedTreeview(content,columns=('Opção','Variação','Preço'),show='headings',height=5)
        for c,w in [('Opção',210),('Variação',270),('Preço',160)]:tree.heading(c,text=c);tree.column(c,width=w)
        tree.pack(fill='x',padx=28,pady=8)
        entries=[dict(id=v['id'],option=v['option_name'] or 'Cor',value=v['value_name'] or v['name'],pack_cents=v['pack_cents']) for v in self.store.variants(m['id'],True)] if m else []
        def redraw():
            from core import money
            tree.delete(*tree.get_children())
            for i,v in enumerate(entries):tree.insert('','end',iid=str(i),values=(v['option'],v['value'],money(v['pack_cents']) if v['pack_cents'] is not None else 'Preço padrão'))
        def add():
            try:
                if not option.get().strip() or not value.get().strip():raise ValueError('Preencha opção e variação.')
                entries.append(dict(option=option.get().strip(),value=value.get().strip(),pack_cents=cents(vp.get(),allow_empty=True)))
                value.delete(0,'end');vp.delete(0,'end');redraw()
            except ValueError as exc:self.fail(exc,win)
        def remove():
            if tree.selection():entries.pop(int(tree.selection()[0]));redraw()
        def load_row(_=None):
            if tree.selection():
                v=entries[int(tree.selection()[0])]
                for w,t in [(option,v['option']),(value,v['value']),(vp,'' if v['pack_cents'] is None else str(v['pack_cents']/100))]:w.delete(0,'end');w.insert(0,t)
        def update():
            if not tree.selection():return
            try:
                v=entries[int(tree.selection()[0])];v.update(option=option.get().strip(),value=value.get().strip(),pack_cents=cents(vp.get(),allow_empty=True));redraw()
            except ValueError as exc:self.fail(exc,win)
        actions=tk.Frame(content,bg=SURFACE);actions.pack(fill='x',padx=28)
        for label,cmd in [('Adicionar opção / variação',add),('Alterar selecionada',update),('Remover',remove)]:button(actions,label,cmd,False).pack(side='left',padx=4)
        tree.bind('<<TreeviewSelect>>',load_row);redraw()
        def save():
            try:
                saved=self.store.save_material(id=m['id'] if m else None,name=name.get(),code=code.get(),size=size.get(),grammage=gram.get(),
                    specification=spec.get(),unit=unit.get(),pack_qty=quantity(qty.get()),pack_cents=cents(price.get()),price_date=parse_date(dt.get()),
                    category=category.get(),variant_options=entries)
                win.destroy()
                if parent and parent.winfo_exists():parent.grab_set()
                if on_saved:on_saved(saved)
                else:self.render()
            except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,win)
        button(foot,'Salvar insumo',save).pack(side='right')

    def product_page(self):
        from app import button
        from core import money,fmt_qty
        bar=self.toolbar('Produtos, versões e composição.', [('Novo produto',lambda:self.product_dialog(),True),
            ('Editar',self.edit_product,False),('Criar variação',self.new_product_variation,False),('Ativar / inativar',self.toggle_product,False)])
        menu=tk.Menu(bar,tearoff=0);menu.add_command(label='Importar CSV',command=self.import_products_dialog);menu.add_command(label='Baixar modelo CSV',command=self.download_product_template)
        btn=button(bar,'⇩',lambda:menu.tk_popup(btn.winfo_rootx(),btn.winfo_rooty()+btn.winfo_height()),False);btn.pack(side='right',padx=4,before=bar.winfo_children()[1])
        filters=self.collapsible_filters();query=tk.StringVar();state=tk.StringVar(value='Todos')
        ttk.Label(filters,text='Nome / código / variação').pack(side='left');ttk.Entry(filters,textvariable=query,width=40).pack(side='left',padx=8)
        ttk.Combobox(filters,textvariable=state,values=('Todos','Ativo','Inativo'),state='readonly',width=12).pack(side='left')
        box=tk.Frame(self.main,bg=BG);box.pack(fill='x',padx=26,pady=8)
        cols=('Código','Variação','Rendimento','Folhas/lote','Kits','Custo/un.','Sugerido/un.','Estado')
        self.tree=StripedTreeview(box,columns=cols,show='tree headings',height=9)
        self.tree.heading('#0',text='Produto / árvore de variações');self.tree.column('#0',width=235)
        for c in cols:self.tree.heading(c,text=c);self.tree.column(c,width=110,minwidth=75)
        self.tree.pack(fill='x');hs=ttk.Scrollbar(box,orient='horizontal',command=self.tree.xview);hs.pack(fill='x');self.tree.configure(xscrollcommand=hs.set)
        sums=tk.Label(self.main,bg=BG,fg=RED,anchor='e');sums.pack(fill='x',padx=28)
        tabs=ttk.Notebook(self.main);tabs.pack(fill='both',expand=True,padx=26,pady=10);details={}
        for category in ('Produção','Embalagem'):
            f=tk.Frame(tabs,bg=SURFACE);tabs.add(f,text='Composição · '+category)
            t=StripedTreeview(f,columns=('Quantidade','Unidade','Folhas','Custo'),show='tree headings',height=6)
            t.heading('#0',text='Insumo / opção / variação');t.column('#0',width=400)
            for c in t['columns']:t.heading(c,text=c);t.column(c,width=120)
            t.pack(fill='both',expand=True);details[category]=t
        def detail(_=None):
            for t in details.values():t.delete(*t.get_children())
            if not self.tree.selection():return
            pid=int(self.tree.selection()[0]);selected=self.store.choices(pid)
            for r in self.store.recipe(pid):
                t=details[r['category'] or 'Produção'];cost=r['qty']*r['pack_cents']/r['pack_qty'] if r['material_name'] else None
                node=t.insert('','end',text=r['material_name'] or r['material_code'],values=(fmt_qty(r['qty']),r['unit'],fmt_qty(r['qty']) if 'folha' in (r['unit'] or '').lower() or (r['unit'] or '').upper()=='A4' else '—',money(rounded(cost)) if cost is not None else 'Revisar'),open=True)
                for v in self.store.variants(r['material_id'],True) if r['material_id'] else []:
                    if r['material_id'] in selected and selected[r['material_id']]!=v['id']:continue
                    t.insert(node,'end',text=v['name'],values=('','', '',money(self.store.material_price(r['material_id'],v['id']))+' / embalagem'))
        def fill(*_):
            self.tree.delete(*self.tree.get_children());total=0;base=0;missing=0
            rows=[p for p in self.store.products() if query.get().casefold() in (p['name']+' '+p['code']+' '+p['variation']).casefold() and (state.get()=='Todos' or bool(p['active'])==(state.get()=='Ativo'))]
            ids={p['id'] for p in rows};pending=list(rows)
            while pending:
                for p in list(pending):
                    parent=str(p['family_id']) if p['family_id'] in ids else ''
                    if parent and not self.tree.exists(parent):continue
                    cost,_=self.store.product_cost(p['id']);suggested,_=self.store.suggested(p)
                    if cost is None:missing+=1
                    else:total+=cost;base+=cost*p['base_yield']
                    sheets=sum(r['qty'] for r in self.store.recipe(p['id']) if 'folha' in (r['unit'] or '').lower() or (r['unit'] or '').upper()=='A4')
                    self.tree.insert(parent,'end',iid=str(p['id']),text=p['name'],open=True,values=(p['code'],p['variation'] or 'Base · maior custo',p['base_yield'],fmt_qty(sheets),p['kits'],money(rounded(cost)) if cost is not None else 'Revisar',money(suggested),'Ativo' if p['active'] else 'Inativo'))
                    pending.remove(p)
            sums.configure(text=f'SOMA custos unitários exibidos: {money(rounded(total))}   |   SOMA custos dos lotes: {money(rounded(base))}   |   {len(rows)} produtos'+(f' • {missing} a revisar' if missing else ''))
            detail()
        for v in (query,state):v.trace_add('write',fill)
        self.tree.bind('<<TreeviewSelect>>',detail);self.tree.bind('<Double-1>',lambda _:self.edit_product());fill()

    def new_product_variation(self):
        pid=self.selection(self.tree)
        if pid:self.product_dialog(self.store.one('SELECT * FROM products WHERE id=?',(pid,)),as_variation=True)

    def product_dialog(self,p=None,as_variation=False):
        from app import field,button
        from core import money,fmt_qty,cents,quantity,automatic_code
        win=self.modal('Nova variação de produto' if as_variation else 'Editar produto' if p else 'Novo produto',970,860)
        foot=tk.Frame(win,bg=SURFACE);foot.pack(side='bottom',fill='x',padx=24,pady=10)
        area=ScrollArea(win,background=SURFACE,min_width=850,min_height=950);area.pack(fill='both',expand=True);content=area.content
        body=tk.Frame(content,bg=SURFACE);body.pack(fill='x',padx=18)
        for col in range(2):body.columnconfigure(col,weight=1)
        name=field(body,'NOME',0,p['name'] if p else '')
        code=field(body,'CÓDIGO ÚNICO',0,(p['code']+'-VAR' if as_variation else p['code']) if p else '',1)
        size=field(body,'TAMANHO',2,p['size'] if p else '')
        gram=field(body,'GRAMATURA',2,p['grammage'] if p else '',1)
        markup=field(body,'MULTIPLICADOR',4,str(p['markup']) if p else '1,8')
        table=field(body,'PREÇO MÍNIMO POR PEÇA • OPCIONAL (R$)',4,str(p['table_cents']/100) if p and p['table_cents'] is not None and not as_variation else '',1)
        produced=field(body,'ESSA COMPOSIÇÃO PRODUZ QUANTAS PEÇAS?',6,p['base_yield'] if p else '1')
        kits=field(body,'QUANTIDADES OFERECIDAS EM KITS • EX.: 1, 6, 12',6,p['kits'] if p else '1',1)
        variation=field(body,'IDENTIFICAÇÃO DA VARIAÇÃO • EX.: HOLOGRÁFICO',8,'' if as_variation else p['variation'] if p else '')
        tk.Label(body,text='Custo mínimo: um lote completo.\nSobra da produção entra no estoque de produtos.',bg=SURFACE,fg=MUTED,justify='left').grid(row=9,column=1,sticky='w',padx=10)
        entries=[(r['material_code'],r['qty']) for r in self.store.recipe(p['id'])] if p else []
        choices=dict(self.store.choices(p['id'])) if p else {}
        mappings={};trees={}
        summary=tk.StringVar()
        def redraw():
            total=0
            for t in trees.values():t.delete(*t.get_children())
            for i,(mc,amount) in enumerate(entries):
                m=self.store.one('SELECT * FROM materials WHERE code=? COLLATE NOCASE',(mc,))
                category=m['category'] if m else 'Produção';t=trees[category]
                cost=amount*self.store.material_price(m['id'],choices.get(m['id']))/m['pack_qty'] if m else 0;total+=cost
                v=self.store.one('SELECT name FROM material_variants WHERE id=?',(choices.get(m['id']),)) if m else None
                t.insert('','end',iid=str(i),text=mc+' · '+(m['name'] if m else 'NÃO ENCONTRADO'),values=(fmt_qty(amount),m['unit'] if m else '',fmt_qty(amount) if m and ('folha' in m['unit'].lower() or m['unit'].upper()=='A4') else '—',v['name'] if v else 'Maior custo',money(rounded(cost))))
            try:
                count=positive_int(produced.get(),'Rendimento');factor=float(markup.get().replace(',','.'))
                if not math.isfinite(factor) or factor<1:raise ValueError('Multiplicador inválido.')
                summary.set(f'SOMA / custo do lote: {money(rounded(total))}  •  Rendimento: {count} peças\nCusto por peça: {money(rounded(total/count))}  •  Sugerido por peça (lote cheio): {money(rounded(total/count*factor))}')
            except ValueError:summary.set('Informe rendimento inteiro positivo e multiplicador válido.')
        for category in ('Produção','Embalagem'):
            group=tk.LabelFrame(content,text=category,bg=SURFACE,fg=OLIVE);group.pack(fill='x',padx=26,pady=8)
            row=tk.Frame(group,bg=SURFACE);row.pack(fill='x',padx=8,pady=6)
            mapping={f"{m['code']} · {m['name']}":m for m in self.store.materials() if m['active'] and m['category']==category};mappings[category]=mapping
            combo=ttk.Combobox(row,values=list(mapping),state='readonly',width=36);combo.pack(side='left',fill='x',expand=True)
            qty=ttk.Entry(row,width=7);qty.insert(0,'1');qty.pack(side='left',padx=5)
            vc=ttk.Combobox(row,values=['Maior custo / todas'],state='readonly',width=24);vc.set('Maior custo / todas');vc.pack(side='left',padx=5)
            def variants(_=None,c=combo,v=vc,mp=mapping):
                m=mp.get(c.get());v.configure(values=['Maior custo / todas']+([r['name'] for r in self.store.variants(m['id'],True)] if m else []));v.set('Maior custo / todas')
            combo.bind('<<ComboboxSelected>>',variants)
            t=StripedTreeview(group,columns=('Qtd','Unidade','Folhas','Opção / variação','Custo'),show='tree headings',height=4);trees[category]=t
            t.heading('#0',text='Insumo');t.column('#0',width=250)
            for col,w in [('Qtd',65),('Unidade',65),('Folhas',65),('Opção / variação',210),('Custo',100)]:t.heading(col,text=col);t.column(col,width=w)
            t.pack(fill='x',padx=8,pady=5)
            def add(c=combo,q=qty,v=vc,mp=mapping):
                try:
                    m=mp.get(c.get())
                    if not m:raise ValueError('Selecione um insumo da categoria.')
                    entries.append((m['code'],quantity(q.get())))
                    if v.get()!='Maior custo / todas':choices[m['id']]=next(r['id'] for r in self.store.variants(m['id'],True) if r['name']==v.get())
                    else:choices.pop(m['id'],None)
                    redraw()
                except ValueError as exc:self.fail(exc,win)
            button(row,'Adicionar',add,False).pack(side='left',padx=3)
            def remove(tree=t):
                if tree.selection():
                    mc,_=entries.pop(int(tree.selection()[0]));m=self.store.one('SELECT id FROM materials WHERE code=?',(mc,))
                    if m and not any(c==mc for c,q in entries):choices.pop(m['id'],None)
                    redraw()
            button(group,'Remover selecionado',remove,False).pack(anchor='e',padx=8,pady=3)
        tk.Label(content,textvariable=summary,bg=SURFACE,fg=RED,justify='left').pack(fill='x',padx=28,pady=8)
        tk.Label(content,text='Variações com preços diferentes geram produtos separados ao salvar.\nPara trocar Brilhante por Holográfico, crie uma variação, remova o BOPP antigo e adicione o novo.',bg=SURFACE,fg=MUTED,justify='left').pack(anchor='w',padx=28)
        for widget in (produced,markup):widget.bind('<KeyRelease>',lambda _:redraw())
        def autocode(_=None):
            if not p and not code.get().strip():code.insert(0,automatic_code(name.get(),size.get(),gram.get()))
        name.bind('<FocusOut>',autocode);redraw()
        def save():
            try:
                if as_variation and not variation.get().strip():raise ValueError('Identifique a variação.')
                with self.store.atomic():
                    pid=self.store.save_product(id=p['id'] if p and not as_variation else None,name=(name.get()+' · '+variation.get().strip()) if as_variation and name.get()==p['name'] else name.get(),code=code.get(),size=size.get(),grammage=gram.get(),
                        markup=float(markup.get().replace(',','.')),table_cents=cents(table.get(),allow_empty=True),recipe=entries,
                        base_yield=positive_int(produced.get(),'Rendimento'),kits=kits.get(),choices=choices,variation=variation.get(),
                        family_id=(p['family_id'] or p['id']) if as_variation else p['family_id'] if p else None)
                    generated=self.store.generate_cost_variations(pid)
                win.destroy();self.render()
                if generated:messagebox.showinfo('Produtos salvos',f'Produto salvo e {len(generated)} versões de custo adicionadas.',parent=self.root)
            except (ValueError,sqlite3.IntegrityError) as exc:self.fail(exc,win)
        button(foot,'Salvar produto e gerar versões de custo',save).pack(side='right')

    def download_product_template(self):
        path=filedialog.asksaveasfilename(parent=self.root,title='Baixar modelo',initialfile='modelo_produtos.csv',defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if path:
            try:Path(path).write_text(self.store.csv_template(),encoding='utf-8-sig');messagebox.showinfo('Modelo salvo','Uma linha por produto. Insumos: CODIGO=quantidade separados por |.\nSubstitua os códigos de exemplo por insumos cadastrados.',parent=self.root)
            except OSError as exc:self.fail(exc,self.root)

    def import_products_dialog(self):
        from app import button,field
        path=filedialog.askopenfilename(parent=self.root,title='Importar produtos',filetypes=[('CSV','*.csv')])
        if not path:return
        try:
            raw=Path(path).read_bytes()
            try:text=raw.decode('utf-8-sig')
            except UnicodeDecodeError:text=raw.decode('cp1252')
            rows=self.store.parse_product_csv(text)
        except (OSError,ValueError) as exc:self.fail(exc,self.root);return
        win=self.modal('Revisar importação CSV',1050,660)
        tk.Label(win,text='Revise as incompatibilidades. Corrija somente a linha selecionada ou ignore os incompatíveis.',bg=SURFACE,fg=OLIVE).pack(anchor='w',padx=24,pady=8)
        tree=StripedTreeview(win,columns=('Linha','Código','Nome','Validação'),show='headings',height=15)
        for c,w in [('Linha',65),('Código',160),('Nome',270),('Validação',470)]:tree.heading(c,text=c);tree.column(c,width=w)
        tree.pack(fill='both',expand=True,padx=24,pady=8)
        valid=[]
        def validate():
            valid.clear();tree.delete(*tree.get_children());codes=set();names=set()
            for i,row in enumerate(rows):
                try:
                    self.store.validate_csv_product(row['data'],codes,names)
                    status='Compatível';valid.append(row);codes.add(row['data']['codigo'].casefold());names.add(row['data']['nome'].casefold())
                except ValueError as exc:status=str(exc)
                tree.insert('','end',iid=str(i),values=(row['line'],row['data']['codigo'],row['data']['nome'],status))
        def correct():
            if not tree.selection():return
            entry=rows[int(tree.selection()[0])];popup=self.modal('Corrigir linha '+str(entry['line']),850,650);popup.transient(win)
            form=tk.Frame(popup,bg=SURFACE);form.pack(fill='x',padx=15);fields={}
            for i,key in enumerate(self.store.CSV_FIELDS):fields[key]=field(form,key.upper(),(i//2)*2,entry['data'][key],i%2,width=38)
            def apply():
                entry['data']={k:v.get().strip() for k,v in fields.items()};popup.destroy();win.grab_set();validate()
            button(popup,'Aplicar correção e validar',apply).pack(side='bottom',pady=15)
        def import_valid(ignore=False):
            validate()
            if len(valid)!=len(rows) and not ignore:
                self.fail(ValueError('Corrija as linhas incompatíveis ou use Ignorar incompatíveis.'),win);return
            added,errors=self.store.import_csv_products(valid)
            if errors:
                rows[:]=errors;validate()
                messagebox.showwarning('Importação parcial',f'{len(added)} produtos adicionados. Revise as linhas restantes.',parent=win)
            else:
                ignored=len(rows)-len(valid);win.destroy();self.render()
                messagebox.showinfo('Importação concluída',f'✓ {len(added)} produtos adicionados\n{ignored} linhas ignoradas.',parent=self.root)
        foot=tk.Frame(win,bg=SURFACE);foot.pack(fill='x',padx=24,pady=12)
        for label,cmd in [('Corrigir selecionado',correct),('Importar todos',import_valid),('Ignorar incompatíveis e importar',lambda:import_valid(True))]:button(foot,label,cmd,False).pack(side='left',padx=4)
        validate()

    def product_stock_panel(self,parent):
        from app import button,field
        from core import fmt_qty,money
        box=tk.LabelFrame(parent,text='Estoque de produtos prontos • independente por versão',bg=BG,fg=OLIVE);box.pack(fill='x',padx=26,pady=8)
        tree=StripedTreeview(box,columns=('Código','Produto','Variação','Saldo','Valor parado'),show='headings',height=5)
        for c,w in [('Código',150),('Produto',280),('Variação',200),('Saldo',90),('Valor parado',150)]:tree.heading(c,text=c);tree.column(c,width=w)
        tree.pack(fill='x',padx=8,pady=5)
        for p in self.store.product_stock():tree.insert('','end',iid=str(p['id']),values=(p['code'],p['name'],p['variation'],fmt_qty(p['balance']),money(rounded(max(0,p['balance'])*(p['cost_unit_cents'] or 0)))))
        def adjust():
            if not tree.selection():return
            pid=int(tree.selection()[0]);win=self.modal('Ajustar estoque de produto',560,390)
            form=tk.Frame(win,bg=SURFACE);form.pack(fill='x',padx=18)
            amount=field(form,'QUANTIDADE EM PEÇAS',0,'1');reason=field(form,'MOTIVO',2,'')
            action=ttk.Combobox(form,values=('Entrada','Retirada','Definir saldo'),state='readonly');action.set('Entrada');action.grid(row=4,column=0,sticky='ew',padx=10,pady=12)
            def save():
                try:
                    q=int(amount.get())
                    self.store.adjust_product_stock(pid,{'Entrada':'entry','Retirada':'out','Definir saldo':'adjustment'}[action.get()],q,reason.get())
                    win.destroy();self.render()
                except ValueError as exc:self.fail(exc,win)
            button(win,'Registrar',save).pack(side='bottom',pady=18)
        def history():
            if not tree.selection():return
            win=self.modal('Histórico do produto',800,440);t=StripedTreeview(win,columns=('Data','Movimento','Quantidade','Motivo'),show='headings')
            for c in t['columns']:t.heading(c,text=c);t.column(c,width=180)
            t.pack(fill='both',expand=True,padx=20,pady=20)
            for r in self.store.all('SELECT * FROM product_movements WHERE product_id=? ORDER BY id DESC',(int(tree.selection()[0]),)):t.insert('','end',values=(r['created_at'],r['kind'],fmt_qty(r['delta']),r['notes']))
        actions=tk.Frame(box,bg=BG);actions.pack(fill='x',padx=8,pady=4)
        button(actions,'Entrada / retirada / ajuste de produto',adjust,False).pack(side='left');button(actions,'Histórico',history,False).pack(side='left',padx=6)
