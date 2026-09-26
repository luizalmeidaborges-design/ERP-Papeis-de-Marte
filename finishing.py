"""Acabamentos por item, com custo e materiais registrados no pedido."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date


def rounded(value):
    return int(Decimal(str(value)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))


class Finishing:
    def init_finishing(self):
        self.db.executescript('''CREATE TABLE IF NOT EXISTS finishes (
            key TEXT PRIMARY KEY, name TEXT NOT NULL,
            material_id INTEGER NOT NULL REFERENCES materials(id),
            extra_cents INTEGER NOT NULL CHECK(extra_cents>=0));''')
        columns={r['name'] for r in self.all('PRAGMA table_info(order_items)')}
        with self.db:
            for name,kind in [('finish_key','TEXT'),('finish_name','TEXT'),('finish_source_id','INTEGER'),
                              ('finish_material_id','INTEGER'),('cost_unit_cents','REAL')]:
                if name not in columns:self.db.execute(f'ALTER TABLE order_items ADD COLUMN {name} {kind}')
        columns={r['name'] for r in self.all('PRAGMA table_info(products)')}
        with self.db:
            for name,kind in [('cost_total_cents','REAL'),('cost_unit_cents','REAL'),('suggested_cents','INTEGER')]:
                if name not in columns:self.db.execute(f'ALTER TABLE products ADD COLUMN {name} {kind}')
        total='''(SELECT CASE WHEN COUNT(*)>0 AND COUNT(*)=COUNT(m.id)
                    THEN SUM(r.qty*m.pack_cents/m.pack_qty) ELSE NULL END
                    FROM recipes r LEFT JOIN materials m ON m.code=r.material_code COLLATE NOCASE
                    WHERE r.product_id=products.id)'''
        update=f'''UPDATE products SET cost_total_cents={total},
            cost_unit_cents={total}/base_yield,
            suggested_cents=CAST(ROUND(({total}/base_yield)*markup) AS INTEGER);'''
        self.db.executescript(update)
        # Cached fields stay current even when prices change through purchasing.
        for table,events in [('recipes',['INSERT','UPDATE','DELETE']),('materials',['INSERT','UPDATE','DELETE']),
                             ('products',['INSERT','UPDATE OF base_yield,markup'])]:
            for event in events:
                name='pricing_'+table+'_'+event.split()[0].lower()
                self.db.executescript(f'CREATE TRIGGER IF NOT EXISTS {name} AFTER {event} ON {table} BEGIN {update} END;')

    def ensure_finish_catalog(self):
        defaults=[('brilhante','Brilhante','BOPBRI30','BOPP Brilhante 30μ',0),
                  ('fosco','Fosco Anti-risco','BOPFOS30','BOPP Fosco Anti-risco 30μ',300),
                  ('holografico','Holográfico','BOPHOL30','BOPP Holográfico 30μ',500)]
        with self.db:
            for key,label,code,name,extra in defaults:
                if self.one('SELECT 1 FROM finishes WHERE key=?',(key,)):continue
                material=self.one('SELECT * FROM materials WHERE code=? COLLATE NOCASE',(code,))
                if material is None:
                    mid=self.db.execute('''INSERT INTO materials(code,name,size,grammage,pack_qty,unit,pack_cents,specification)
                        VALUES(?,?, 'A4','30μ',1,'Folha A4',0,'Configurar preço do rolo e rendimento em folhas A4 antes de usar.')''',
                        (code,name)).lastrowid
                else:
                    if material['name']!=name:raise ValueError(f'Código reservado de acabamento já usado: {code}')
                    mid=material['id']
                self.db.execute('INSERT INTO finishes VALUES(?,?,?,?)',(key,label,mid,extra))

    def finishes(self):
        return self.all("SELECT f.*,m.name AS material_name,m.code,m.pack_qty,m.pack_cents FROM finishes f JOIN materials m ON m.id=f.material_id ORDER BY CASE f.key WHEN 'brilhante' THEN 0 WHEN 'fosco' THEN 1 ELSE 2 END")

    def configure_finishes(self, rows):
        if {r['key'] for r in rows}!={'brilhante','fosco','holografico'} or len(rows)!=3:
            raise ValueError('Configure os três acabamentos.')
        if len({r['material_id'] for r in rows})!=3:raise ValueError('Cada acabamento precisa de um insumo independente.')
        with self.db:
            for r in rows:
                m=self.one('SELECT * FROM materials WHERE id=? AND active=1',(r['material_id'],))
                if not m or self.variants(m['id']):raise ValueError('Vincule insumos ativos e independentes, sem variações de cor.')
                if not isinstance(r['extra_cents'],int) or r['extra_cents']<0:raise ValueError('Adicional inválido.')
                if r['key']=='brilhante' and r['extra_cents']!=0:raise ValueError('Brilhante deve ter adicional zero.')
                if 'pack_qty' in r:
                    import math
                    if not math.isfinite(r['pack_qty']) or r['pack_qty']<=0 or r['pack_cents']<=0:
                        raise ValueError('Informe o valor do rolo/embalagem e quantas folhas A4 úteis ele rende.')
                    self.db.execute('UPDATE materials SET pack_qty=?,pack_cents=?,price_date=? WHERE id=?',
                        (r['pack_qty'],r['pack_cents'],date.today().isoformat(),m['id']))
                self.db.execute('UPDATE finishes SET material_id=?,extra_cents=? WHERE key=?',(m['id'],r['extra_cents'],r['key']))

    def laminated(self, product_id):
        standard=self.one("SELECT material_id FROM finishes WHERE key='brilhante'")
        return bool(standard and self.one('''SELECT 1 FROM recipes r JOIN materials m ON m.code=r.material_code COLLATE NOCASE
                         WHERE r.product_id=? AND m.id=?''',(product_id,standard['material_id'])))

    def finish_quote(self, product_id, key='brilhante'):
        product=self.one('SELECT * FROM products WHERE id=?',(product_id,))
        if not product:raise ValueError('Produto não encontrado.')
        cost,missing=self.product_cost(product_id)
        if cost is None:raise ValueError('Revise a composição do produto.')
        if not self.laminated(product_id):
            if key!='brilhante':raise ValueError('O produto não usa o BOPP padrão vinculado em Acabamentos.')
            return dict(cost_unit_cents=cost,unit_cents=product['table_cents'] if product['table_cents'] is not None else rounded(cost*product['markup']))
        standard=self.one("SELECT * FROM finishes WHERE key='brilhante'")
        chosen=self.one('SELECT * FROM finishes WHERE key=?',(key,))
        if not chosen:raise ValueError('Acabamento inválido.')
        source=self.one('SELECT * FROM materials WHERE id=?',(standard['material_id'],))
        target=self.one('SELECT * FROM materials WHERE id=?',(chosen['material_id'],))
        if not source['active'] or not target['active'] or source['pack_cents']<=0 or target['pack_cents']<=0:
            raise ValueError('Configure o custo do BOPP padrão e do acabamento escolhido em Insumos.')
        if self.variants(source['id']) or self.variants(target['id']):raise ValueError('Use BOPP independente, sem variações de cor.')
        amount=sum(r['qty'] for r in self.recipe(product_id) if r['material_code'].casefold()==source['code'].casefold())/product['base_yield']
        cost=cost-amount*source['pack_cents']/source['pack_qty']+amount*target['pack_cents']/target['pack_qty']
        price=rounded(cost*product['markup'])+chosen['extra_cents']
        return dict(finish_key=key,finish_name=chosen['name'],finish_source_id=source['id'],finish_material_id=target['id'],
                    cost_unit_cents=cost,unit_cents=price)
