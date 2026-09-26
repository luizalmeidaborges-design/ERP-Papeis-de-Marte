"""Catálogo, lotes mínimos, clientes e estoque de produtos (build 2.4)."""
import csv
import io
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


def rounded(v):
    return int(Decimal(str(v)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def positive_int(v, label='Quantidade'):
    if isinstance(v,float) and math.isfinite(v) and v.is_integer():v=int(v)
    text=str(v).strip()
    if not re.fullmatch(r'[0-9]+',text) or not 1<=int(text)<=1000000:
        raise ValueError(f'{label}: informe um inteiro entre 1 e 1000000.')
    return int(text)


class Catalog:
    @contextmanager
    def atomic(self):
        name='catalog_'+str(getattr(self,'_depth',0))
        self._depth=getattr(self,'_depth',0)+1
        self.db.execute('SAVEPOINT '+name)
        try:
            yield
            self.db.execute('RELEASE '+name)
        except Exception:
            self.db.execute('ROLLBACK TO '+name);self.db.execute('RELEASE '+name)
            raise
        finally:self._depth-=1

    def init_catalog(self):
        migrations={
            'materials':[('category',"TEXT NOT NULL DEFAULT 'Produção'")],
            'material_variants':[('option_name',"TEXT NOT NULL DEFAULT ''"),('value_name',"TEXT NOT NULL DEFAULT ''"),('pack_cents','INTEGER')],
            'products':[('family_id','INTEGER REFERENCES products(id)'),('variation',"TEXT NOT NULL DEFAULT ''"),('kits',"TEXT NOT NULL DEFAULT '1'")],
            'orders':[('customer_id','INTEGER REFERENCES customers(id)')],
            'order_items':[('pricing_mode',"TEXT NOT NULL DEFAULT 'legacy'"),('stock_source',"TEXT NOT NULL DEFAULT 'production'"),('batches','INTEGER'),('produced_qty','INTEGER'),('usage_json',"TEXT NOT NULL DEFAULT '{}' ")],
        }
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,phone TEXT NOT NULL DEFAULT '',
              email TEXT NOT NULL DEFAULT '',birthday TEXT NOT NULL DEFAULT '',address TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS product_choices(product_id INTEGER NOT NULL REFERENCES products(id),
              material_id INTEGER NOT NULL REFERENCES materials(id),variant_id INTEGER NOT NULL REFERENCES material_variants(id),
              PRIMARY KEY(product_id,material_id));
            CREATE TABLE IF NOT EXISTS product_movements(id INTEGER PRIMARY KEY,product_id INTEGER NOT NULL REFERENCES products(id),
              order_id INTEGER REFERENCES orders(id),delta REAL NOT NULL,kind TEXT NOT NULL,notes TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS product_movements_order ON product_movements(order_id);
        ''')
        with self.db:
            for table,columns in migrations.items():
                known={r['name'] for r in self.all('PRAGMA table_info('+table+')')}
                for key,kind in columns:
                    if key not in known:self.db.execute(f'ALTER TABLE {table} ADD COLUMN {key} {kind}')
        # A fixed variant has its own price; an unspecified variant uses the highest active cost.
        cost='''COALESCE((SELECT COALESCE(v.pack_cents,m.pack_cents) FROM product_choices c JOIN material_variants v ON v.id=c.variant_id
                  WHERE c.product_id=r.product_id AND c.material_id=m.id),
                  (SELECT MAX(COALESCE(v.pack_cents,m.pack_cents)) FROM material_variants v WHERE v.material_id=m.id AND v.active=1),m.pack_cents)'''
        total=f'''(SELECT CASE WHEN COUNT(*)>0 AND COUNT(*)=COUNT(m.id) THEN SUM(r.qty*({cost})/m.pack_qty) ELSE NULL END
                  FROM recipes r LEFT JOIN materials m ON m.code=r.material_code COLLATE NOCASE WHERE r.product_id=products.id)'''
        update=f'''UPDATE products SET cost_total_cents={total},cost_unit_cents={total}/base_yield,
                   suggested_cents=CAST(ROUND(({total}/base_yield)*markup) AS INTEGER);'''
        for t in self.all("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'pricing_%'"):
            self.db.execute('DROP TRIGGER '+t['name'])
        self.db.executescript(update)
        for table,events in [('recipes',['INSERT','UPDATE','DELETE']),('materials',['INSERT','UPDATE','DELETE']),
                             ('material_variants',['INSERT','UPDATE','DELETE']),('product_choices',['INSERT','UPDATE','DELETE']),
                             ('products',['INSERT','UPDATE OF base_yield,markup'])]:
            for event in events:
                self.db.executescript(f'CREATE TRIGGER pricing_{table}_{event.split()[0].lower()} AFTER {event} ON {table} BEGIN {update} END;')

    def material_price(self, material_id, variant_id=None):
        m=self.one('SELECT * FROM materials WHERE id=?',(material_id,))
        if variant_id is not None:
            v=self.one('SELECT * FROM material_variants WHERE id=? AND material_id=?',(variant_id,material_id))
            if not v:raise ValueError('Variação incompatível com o insumo.')
            return v['pack_cents'] if v['pack_cents'] is not None else m['pack_cents']
        prices=[v['pack_cents'] if v['pack_cents'] is not None else m['pack_cents'] for v in self.variants(material_id,True)]
        return max(prices) if prices else m['pack_cents']

    def choices(self,product_id):
        return {r['material_id']:r['variant_id'] for r in self.all('SELECT * FROM product_choices WHERE product_id=?',(product_id,))}

    def kit_quantities(self,text):
        if not str(text).strip():raise ValueError('Informe pelo menos uma quantidade de kit (ex.: 1, 6, 12).')
        return sorted({positive_int(t,'Kit') for t in re.split(r'[,;\s]+',str(text).strip())})

    def customers(self):
        return self.all('SELECT * FROM customers ORDER BY name COLLATE NOCASE,id')

    def save_customer(self,*,id=None,name,phone='',email='',birthday='',address=''):
        name=name.strip();email=email.strip();birthday=birthday.strip()
        if not name:raise ValueError('Informe o nome do cliente.')
        if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise ValueError('E-mail inválido.')
        if birthday:
            try:b=date.fromisoformat(birthday)
            except ValueError:raise ValueError('Data de nascimento inválida.')
            if b>date.today():raise ValueError('O nascimento não pode ser futuro.')
        values=(name,phone.strip(),email,birthday,address.strip())
        with self.atomic():
            if id:
                if not self.one('SELECT 1 FROM customers WHERE id=?',(id,)):raise ValueError('Cliente não encontrado.')
                self.db.execute('UPDATE customers SET name=?,phone=?,email=?,birthday=?,address=? WHERE id=?',values+(id,))
            else:id=self.db.execute('INSERT INTO customers(name,phone,email,birthday,address) VALUES(?,?,?,?,?)',values).lastrowid
        return id

    def product_stock(self):
        return self.all('''SELECT p.*,COALESCE(SUM(m.delta),0) AS balance FROM products p LEFT JOIN product_movements m ON m.product_id=p.id
                           GROUP BY p.id ORDER BY p.name COLLATE NOCASE''')

    def product_move(self,pid,delta,kind,notes,order_id=None):
        self.db.execute('INSERT INTO product_movements(product_id,delta,kind,notes,order_id,created_at) VALUES(?,?,?,?,?,?)',
            (pid,delta,kind,notes,order_id,datetime.now().isoformat(timespec='seconds')))

    def adjust_product_stock(self,pid,action,qty,notes):
        if not notes.strip():raise ValueError('Informe o motivo.')
        if not math.isfinite(qty) or int(qty)!=qty or qty<0:raise ValueError('Informe unidades inteiras, maiores ou iguais a zero.')
        if not self.one('SELECT 1 FROM products WHERE id=?',(pid,)):raise ValueError('Produto não encontrado.')
        balance=self.one('SELECT COALESCE(SUM(delta),0) AS n FROM product_movements WHERE product_id=?',(pid,))['n']
        if action not in ('entry','out','adjustment'):raise ValueError('Movimento inválido.')
        delta=qty-balance if action=='adjustment' else (-qty if action=='out' else qty)
        with self.atomic():self.product_move(pid,delta,action,notes.strip())

    def order_quote(self,pid,qty,source='production',variants=None):
        qty=positive_int(qty,'Quantidade do pedido')
        p=self.one('SELECT * FROM products WHERE id=?',(pid,))
        if not p:raise ValueError('Produto não encontrado.')
        if source not in ('production','stock'):raise ValueError('Origem inválida.')
        selections={int(k):int(v) for k,v in (variants or {}).items()};selections.update(self.choices(pid))
        rows=self.recipe(pid)
        if not rows or any(r['material_name'] is None for r in rows):raise ValueError('Revise a composição do produto.')
        batches=math.ceil(qty/p['base_yield']) if source=='production' else 0
        usage={};cost=0
        for r in rows:
            mid=r['material_id'];vid=selections.get(mid)
            options=self.variants(mid,True)
            if self.variants(mid) and (vid is None or not any(v['id']==vid for v in options)):
                raise ValueError(f"Selecione uma variação ativa de {r['material_name']}.")
            amount=r['qty']*(batches if source=='production' else qty/p['base_yield'])
            cost+=amount*self.material_price(mid,vid)/r['pack_qty']
            if source=='production':
                key=f'{mid}:{vid or 0}';usage[key]=usage.get(key,0)+amount
        # Price table is a per-piece floor; a small production lot still pays a full batch.
        sale=max(cost*p['markup'],(p['table_cents'] or 0)*qty)
        unit=rounded(sale/qty)
        return dict(pricing_mode='batch',stock_source=source,batches=batches,
            produced_qty=batches*p['base_yield'],usage_json=json.dumps(usage,sort_keys=True),
            cost_unit_cents=cost/qty,unit_cents=unit)

    def create_product_variation(self,pid,*,name,code,label,recipe,choices=None):
        p=self.one('SELECT * FROM products WHERE id=?',(pid,))
        if not p:raise ValueError('Produto base não encontrado.')
        return self.save_product(name=name,code=code,size=p['size'],grammage=p['grammage'],markup=p['markup'],table_cents=None,
            recipe=recipe,base_yield=p['base_yield'],kits=p['kits'],family_id=p['family_id'] or pid,variation=label,choices=choices or {})

    def generate_cost_variations(self,pid):
        """Material options of different prices become independent product rows. Unlimited UI rows, capped combinations."""
        import itertools
        p=self.one('SELECT * FROM products WHERE id=?',(pid,));recipe=self.recipe(pid);fixed=self.choices(pid)
        variable=[]
        for mid in dict.fromkeys(r['material_id'] for r in recipe):
            opts=self.variants(mid,True)
            if mid not in fixed and len({self.material_price(mid,v['id']) for v in opts})>1:variable.append((mid,opts))
        if not variable:return []
        count=math.prod(len(opts) for _,opts in variable)
        if count>1000:raise ValueError(f'{count} combinações de custo. Divida o cadastro em grupos menores (máximo 1000 por vez).')
        created=[]
        with self.atomic():
            for combination in itertools.product(*(opts for _,opts in variable)):
                ids='-'.join(str(v['id']) for v in combination)
                code=f"{p['code']}-V{ids}"
                if self.one('SELECT 1 FROM products WHERE code=?',(code,)):continue
                label=' / '.join(v['name'] for v in combination)
                selected=dict(fixed);selected.update({mid:v['id'] for (mid,_),v in zip(variable,combination)})
                created.append(self.create_product_variation(pid,name=p['name']+' · '+label,code=code,label=label,
                    recipe=[(r['material_code'],r['qty']) for r in recipe],choices=selected))
        return created

    CSV_FIELDS=('nome','codigo','tamanho','gramatura','rendimento','multiplicador','kits','preco_unitario','insumos','variacoes')

    def csv_template(self):
        out=io.StringIO();writer=csv.DictWriter(out,fieldnames=self.CSV_FIELDS,delimiter=';');writer.writeheader()
        writer.writerow(dict(nome='Marca-página exemplo',codigo='MAR-EXEMPLO',tamanho='A6',gramatura='180',rendimento='6',
            multiplicador='1,8',kits='1|6|12',preco_unitario='',insumos='CODIGO_PAPEL=1|CODIGO_EMBALAGEM=6',variacoes=''))
        return out.getvalue()

    def parse_product_csv(self,text):
        text=text.lstrip('\ufeff')
        if not text.strip():raise ValueError('O arquivo está vazio.')
        delimiter=';' if ';' in text.splitlines()[0] else ','
        reader=csv.DictReader(io.StringIO(text),delimiter=delimiter)
        if not reader.fieldnames or set(reader.fieldnames)!=set(self.CSV_FIELDS):raise ValueError('Cabeçalhos incompatíveis. Baixe o modelo CSV e mantenha todas as colunas.')
        rows=[]
        for row in reader:
            if None in row:raise ValueError(f'Colunas excedentes na linha {reader.line_num}. Use o separador do modelo.')
            rows.append(dict(line=reader.line_num,data={k:(v or '').strip() for k,v in row.items()}))
        if not rows:raise ValueError('O arquivo não contém produtos.')
        return rows

    def validate_csv_product(self,row,seen_codes=None,seen_names=None):
        from core import cents
        if not row['nome'].strip() or not row['codigo'].strip():raise ValueError('Nome e código são obrigatórios.')
        if self.one('SELECT 1 FROM products WHERE code=? COLLATE NOCASE',(row['codigo'],)) or row['codigo'].casefold() in (seen_codes or set()):raise ValueError('Código já cadastrado ou repetido no CSV.')
        if self.one('SELECT 1 FROM products WHERE name=? COLLATE NOCASE',(row['nome'],)) or row['nome'].casefold() in (seen_names or set()):raise ValueError('Nome já cadastrado ou repetido no CSV. Identifique a variação no nome.')
        recipe=[]
        for part in row['insumos'].split('|'):
            if '=' not in part:raise ValueError('Composição: use CODIGO=quantidade|CODIGO=quantidade.')
            code,q=part.rsplit('=',1)
            try:qty=float(q.replace(',','.'))
            except ValueError:raise ValueError('Quantidade de insumo inválida.')
            if not math.isfinite(qty) or qty<=0:raise ValueError('Quantidade de insumo deve ser positiva.')
            m=self.one('SELECT * FROM materials WHERE code=? COLLATE NOCASE AND active=1',(code.strip(),))
            if not m:raise ValueError('Insumo ausente ou inativo: '+code)
            recipe.append((m['code'],qty))
        try:markup=float(row['multiplicador'].replace(',','.'))
        except ValueError:raise ValueError('Multiplicador inválido.')
        if not math.isfinite(markup) or markup<1:raise ValueError('Multiplicador deve ser no mínimo 1.')
        choices={}
        for entry in filter(None,row['variacoes'].split('|')):
            if '=' not in entry:raise ValueError('Variações: use CODIGO=Opção · Variação.')
            code,label=entry.split('=',1)
            v=self.one('SELECT v.* FROM material_variants v JOIN materials m ON m.id=v.material_id WHERE m.code=? COLLATE NOCASE AND v.name=? COLLATE NOCASE AND v.active=1',(code.strip(),label.strip()))
            if not v:raise ValueError('Variação não encontrada: '+entry)
            if code.strip().casefold() not in {c.casefold() for c,q in recipe}:raise ValueError('Variação não pertence à composição: '+code)
            choices[v['material_id']]=v['id']
        return dict(name=row['nome'],code=row['codigo'],size=row['tamanho'],grammage=row['gramatura'],
            base_yield=positive_int(row['rendimento'],'Rendimento'),markup=markup,table_cents=cents(row['preco_unitario'],allow_empty=True),
            kits=','.join(map(str,self.kit_quantities(row['kits'].replace('|',',')))),recipe=recipe,choices=choices)

    def import_csv_products(self,rows):
        added=[];errors=[]
        for entry in rows:
            try:
                with self.atomic():
                    data=self.validate_csv_product(entry['data'])
                    pid=self.save_product(**data);generated=self.generate_cost_variations(pid)
                    added.extend([pid]+generated)
            except (ValueError,sqlite3.IntegrityError) as exc:errors.append(dict(entry,error=str(exc)))
        return added,errors
