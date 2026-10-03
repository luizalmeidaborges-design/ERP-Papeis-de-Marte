"""Composição multinível por identidade do produto, com consumo por unidade."""
import math


class ProductComposition:
    def init_composition(self):
        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS product_components (
                product_id INTEGER NOT NULL REFERENCES products(id),
                position INTEGER NOT NULL,
                component_id INTEGER NOT NULL REFERENCES products(id),
                qty REAL NOT NULL CHECK(qty>0),
                section TEXT NOT NULL CHECK(section IN ('Produção','Embalagem')),
                PRIMARY KEY(product_id,position), CHECK(product_id<>component_id))''')
            self.db.execute('CREATE INDEX IF NOT EXISTS component_parent ON product_components(component_id)')

    def components(self,product_id):
        return self.all('''SELECT c.*,p.code,p.name,p.active FROM product_components c
            JOIN products p ON p.id=c.component_id WHERE c.product_id=? ORDER BY c.position''',(product_id,))

    def expanded_recipe(self,product_id):
        """Return aggregated leaf materials for ONE sold unit, including legacy yields.

        Memoization is scoped to this calculation; a subsequent material/recipe
        edit always uses current data. A recursion stack distinguishes shared
        children from cycles. No database mutation occurs during expansion.
        """
        memo={};visiting=set()
        def expand(pid):
            if pid in visiting:raise ValueError('Composição circular: um produto não pode conter ele mesmo, direta ou indiretamente.')
            if pid in memo:return memo[pid]
            if len(visiting)>=100:raise ValueError('Composição excede o limite de 100 níveis.')
            p=self.one('SELECT code,base_yield FROM products WHERE id=?',(pid,))
            if not p:raise ValueError('Produto da composição não encontrado.')
            visiting.add(pid)
            rows=self.recipe(pid);children=self.components(pid)
            if not rows and not children:raise ValueError(f"Composição vazia: {p['code']}.")
            result={}
            def add(row,amount):
                if not math.isfinite(amount) or amount<=0:raise ValueError('Quantidade da composição inválida.')
                key=row['material_code'].casefold()
                if key not in result:result[key]=dict(row,qty=0)
                result[key]['qty']+=amount
                if not math.isfinite(result[key]['qty']):raise ValueError('Quantidade acumulada inválida.')
            for r in rows:
                if r['material_name'] is None:raise ValueError(f"Insumo não encontrado: {r['material_code']}.")
                add(r,r['qty']/p['base_yield'])
            for child in children:
                for r in expand(child['component_id']).values():
                    add(r,r['qty']*child['qty']/p['base_yield'])
            visiting.remove(pid);memo[pid]=result
            return result
        return list(expand(product_id).values())
