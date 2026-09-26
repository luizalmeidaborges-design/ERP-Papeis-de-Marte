# ERP Papéis de Marte

Aplicativo **offline** para Windows, escrito em Python com Tkinter e SQLite.
O arquivo `.exe` é gerado no próprio Windows. Não é necessário manter Excel
nem Python no computador que receber o executável pronto.

## Para usar agora no VS Code

1. Abra esta pasta no VS Code e abra o terminal (**Terminal > Novo Terminal**).
2. Instale as dependências e inicie a interface (se `py` não existir,
   substitua `py -3` por `python` na primeira linha):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Para gerar o EXE

Execute `compilar_windows.bat` nesta pasta (pelo Explorador de Arquivos ou pelo
terminal do VS Code). O resultado será `dist\ERP_Papeis_de_Marte.exe`.
O script aceita Python 3.10+ instalado como `py -3` **ou** `python`.
O computador de compilação precisa de Python 3 e conexão à internet na primeira
instalação das dependências. O EXE gerado funciona sem internet.

## Atualizações automáticas

**No GitHub:** após colocar este projeto em um repositório público, abra
**Actions → Compilar e publicar ERP → Run workflow**, informe `1.1.0` para a
primeira publicação e execute. O próprio GitHub compila no Windows, calcula a
conferência do EXE e cria a Release. Faça o download do EXE da primeira Release
e envie uma vez à cliente. Para atualizações seguintes, repita a ação com
`1.2.0`, `1.3.0` etc., sempre aumentando a versão. A cliente não precisa de
uma conta no GitHub nem instalar o GitHub CLI. O botão de publicação aparece
depois que `.github/workflows/publicar.yml` estiver no ramo padrão.

Também é possível publicar ao alterar `release-version.txt` no ramo `main`:
primeiro envie as mudanças do programa e depois atualize esse arquivo para a
próxima versão (por exemplo, `1.3.0`). O GitHub inicia a compilação automaticamente.
Mantenha apenas uma versão nova por publicação; a Release recebe o EXE e
`update.json`. O comando manual continua disponível na aba Actions.

Para criar o repositório `luizalmeidaborges-design/ERP-Papeis-de-Marte`
diretamente do seu Windows, instale [Git for Windows](https://git-scm.com/download/win)
e [GitHub CLI](https://cli.github.com/), execute `gh auth login` no terminal uma
vez e abra `criar_repositorio_windows.bat` na pasta extraída do ZIP. O script
confere que a planilha privada está excluída, cria o repositório **público** e
envia o projeto. Em seguida, use **Actions → Compilar e publicar ERP** no GitHub.

Quando receber arquivos atualizados do projeto, copie-os para **a mesma pasta**
onde executou `criar_repositorio_windows.bat`, substituindo os anteriores e
preservando a pasta `.git`. Execute `enviar_alteracoes_windows.bat`; depois abra
Actions e publique com uma versão maior. Enviar o código e executar a publicação
são duas etapas diferentes. Não copie bancos `.db` nem a planilha privada para
o repositório.

O repositório público inclui o código e o logo, mas exclui a planilha privada
`assets/Precificação.xlsx`, bancos SQLite e arquivos temporários. O EXE publicado
inicia com os dados já existentes no computador da cliente. O banco é copiado
automaticamente durante o uso e quando o programa é fechado.

**Primeira entrega:** o EXE já enviado à cliente não conhece o atualizador.
Envie uma única vez um novo EXE compilado com esta versão, depois de configurar
o endereço de publicação. A partir daí, quando ela abrir o aplicativo com
internet, ele consulta a versão mais recente e baixa o novo EXE em segundo plano.
Uma mensagem no menu lateral avisa quando a versão estiver pronta. Na abertura
seguinte, o EXE anterior inicia a versão baixada automaticamente, inclusive
sem internet. Mantenha o EXE inicial no mesmo lugar para a cliente usá-lo
sempre; ele encaminhará para a versão atual. O banco `marte.db` continua em
`%LOCALAPPDATA%\ERP_Papeis_de_Marte`.

**Preparar publicação (exemplo com GitHub Releases público):**

1. Crie um repositório público com um README inicial para publicar os executáveis. Anote `USUARIO/REPO`.
2. Em `assets/update_config.json`, escreva a versão atual e coloque em
   `manifest_url` este endereço, substituindo `USUARIO/REPO`:
   `https://github.com/USUARIO/REPO/releases/latest/download/update.json`.
   O arquivo distribuído neste ZIP vem com URL vazia; enquanto ela estiver vazia,
   a consulta automática fica desligada.
3. Execute `compilar_windows.bat` no Windows e, no terminal nesta pasta, execute
   `py -3 gerar_manifesto.py --repo USUARIO/REPO` (pode usar `python` no lugar de
   `py -3`). O comando cria `dist\update.json` usando o tamanho e SHA-256 do EXE
   recém-compilado.
4. No repositório, crie uma Release com tag `v1.1.0` (ou `v` + a versão do JSON).
   Anexe, com estes nomes exatos, `dist\ERP_Papeis_de_Marte.exe` e
   `dist\update.json`. Publique a Release.
5. Depois de conferir que o endereço `.../releases/latest/download/update.json`
   abre, mande o novo EXE à cliente para esta única troca manual.

**Próximas versões:** aumente `version` em `assets/update_config.json` (por
exemplo `1.2.0`), preserve o mesmo `manifest_url`, compile de novo e execute
`py -3 gerar_manifesto.py --repo USUARIO/REPO`. Crie a Release `v1.2.0`, anexe
o novo EXE e seu `update.json` e publique. Não altere os arquivos depois de
gerar o manifesto: se recompilar, gere um manifesto novo. Não publique como
*pré-lançamento*, pois o endereço `latest` usa a release normal mais recente.

**Publicação com um comando:** depois de instalar o [GitHub CLI](https://cli.github.com/)
e executar `gh auth login` uma vez no seu computador, abra o terminal nesta
pasta e execute `publicar_windows.bat USUARIO/REPO 1.2.0`. O script configura
o endereço e a versão, chama a compilação (que pede uma tecla ao terminar),
gera o manifesto e publica uma Release normal com os dois arquivos.
Na primeira vez, use `1.1.0` e envie o EXE resultante uma vez à cliente.
Nas próximas vezes, escolha um número de versão maior. O repositório precisa
existir e estar público; a máquina que publica precisa de internet.

O computador da cliente continua funcionando offline quando não consegue
consultar ou baixar a atualização. Somente a consulta precisa de internet.
Releases e arquivos precisam estar acessíveis sem login, pois o EXE não inclui
credenciais. O download é feito por HTTPS e conferido pelo tamanho e SHA-256
declarados no manifesto; controle o acesso de publicação desse repositório.

## Uso

- **Insumos:** nome, tamanho, gramatura, observações, preço e quantidade da embalagem.
  O custo unitário é calculado como preço ÷ quantidade. Para comprimento ou massa,
  use a unidade adequada e mantenha a quantidade da receita na mesma unidade.
- **Tamanho e gramatura:** aparecem em colunas separadas nos insumos e nos
  produtos. Nos insumos, um novo código é gerado automaticamente com três caracteres do nome,
  tamanho e gramatura. Exemplo: Offset + A4 + 150 = `OFFA4150`. Os códigos dos
  registros anteriores são preservados na atualização. Nos produtos, o código é
  preenchido manualmente e precisa ser único; também pode ser editado.
- **Variações de insumos:** no cadastro, liste cores como `Branco, Dourado, Preto`.
  O preço e o custo unitário continuam sendo do insumo, iguais para todas as
  cores. Ao selecionar no pedido um produto que usa esse insumo, escolha a cor
  de cada material antes de adicionar o item. Se o mesmo produto tiver cores
  diferentes, adicione-o em linhas separadas. A escolha aparece no pedido e no
  PDF.
- **Produtos:** acrescente quantos insumos quiser à composição de uma unidade.
  O preço sugerido é custo × multiplicador (padrão 1,8, igual à planilha). O preço
  de tabela pode ser definido separadamente. A média vendida é o total efetivamente
  cobrado pelo produto dividido pela quantidade vendida nos pedidos vinculados.
- **Pedidos:** cliente, entrega, vários itens, valor por item, status de pagamento,
  status de produção, observações e geração de comprovante em PDF. Produtos do
  cadastro aparecem como sugestões; também é possível digitar itens avulsos.
  Clique no botão de calendário ao lado de **Entrega** para escolher a data.
  Quando o pagamento for **Parcial**, informe quanto já foi recebido; o saldo
  aparece no pedido e na coluna **Restante**. **Pago** encerra o saldo; **Pendente**
  mostra o total em aberto. Pedidos anteriores preservam seus status.
  Selecione um pedido e use **Excluir pedido** para removê-lo após confirmação.
  O estoque consumido é devolvido às variações correspondentes, com estorno
  registrado no histórico. O número do pedido não é reutilizado.
  O botão **Salvar pedido** permanece visível no rodapé da edição; use a barra
  de rolagem para alcançar os demais campos em telas menores.
- **Calendário:** veja as entregas do mês, mude de mês e clique em um dia para
  listar seus pedidos. Um clique duplo na lista abre o pedido para edição.
- **Filtros de pedidos:** filtros independentes por número, cliente, itens, data
  de criação, data de entrega, pagamento, produção, faixa de valor e valor
  restante. Datas são
  pesquisadas como aparecem na tabela (`DD/MM/AAAA`).
- **Relatórios:** escolha mês/ano de cadastro ou Total para ver pedidos, receita,
  ticket médio, situação e itens vendidos. Exporte o resumo para PDF.
- **Estoque:** registre entrada de insumos, retirada forçada e ajuste para um
  saldo final contado. Cada operação exige motivo e fica no histórico. Pedidos
  novos com produtos cadastrados retiram automaticamente os insumos da receita
  na data do cadastro, usando quantidade do pedido × quantidade da composição.
  Pedidos com itens avulsos não têm baixa automática. Ao mudar os itens de um
  pedido, a retirada anterior é estornada e refeita; mudar apenas pagamento,
  produção, preço ou entrega não altera o estoque. Produtos com composição
  incompleta precisam ser corrigidos para terem retirada automática.
  O saldo e o histórico aparecem por variação. **Transferir** move unidades
  entre cores ou do saldo antigo “Sem variação (legado)” para uma cor, sem mudar
  a quantidade total do insumo.
- **Início:** totais e pedidos em aberto por data de entrega.
- **Salvar cópia dos dados:** crie regularmente um arquivo `.db` de backup.

## Backup automático (a partir da versão 1.2.1)

O programa mantém uma cópia diária do banco em
`%LOCALAPPDATA%\ERP_Papeis_de_Marte\backups\marte_AAAA-MM-DD.db`.
Cria a primeira cópia ao abrir, atualiza a cópia após mudanças (verificação a
cada 30 segundos) e faz outra cópia ao clicar no **X**. No fechamento, aparece
**Backup sendo realizado** e o programa aguarda a cópia local e a cópia para a
pasta escolhida terminarem. Cópias dos dias anteriores continuam disponíveis;
no mesmo dia, a cópia é atualizada com os pedidos e cadastros mais recentes.

Clique no pequeno ícone **📁** ao lado da data no topo para escolher uma pasta
de backup. Se escolher uma pasta sincronizada pelo OneDrive ou Google Drive, o
aplicativo copia os arquivos para ela e o serviço sincroniza com a nuvem quando
houver conexão. Confira o ícone do serviço para saber se o envio terminou: o
aviso de backup do ERP confirma a cópia na pasta, não o envio à nuvem. Se essa
pasta ficar indisponível, o backup local continua sendo salvo e aparece um
aviso; ao voltar, o aplicativo tenta copiar novamente. O banco de trabalho
`marte.db` permanece fora da pasta sincronizada.

Para recuperar um backup, feche o ERP, guarde uma cópia do `marte.db` atual e
copie o arquivo de backup escolhido para
`%LOCALAPPDATA%\ERP_Papeis_de_Marte\marte.db`, substituindo o arquivo anterior.
Ao abrir, o aplicativo carregará os dados daquela cópia.

O banco fica em `%LOCALAPPDATA%\ERP_Papeis_de_Marte\marte.db` no Windows.
Ao instalar uma nova versão do EXE, o aplicativo atualiza os campos necessários
no banco existente e mantém cadastros, pedidos e códigos já salvos.
O EXE enviado anteriormente importava o Excel em `assets` **somente no primeiro uso**.
A partir desta versão, o EXE publicado não inclui a planilha de pedidos e preços
da cliente. Bancos existentes mantêm todos os dados; uma instalação nova começa
com cadastros vazios. Ao executar o código localmente com a planilha presente,
ela ainda é importada apenas no primeiro uso. A planilha está excluída do Git.
Os oito pedidos históricos importados não têm data de entrega na
planilha; ela aparece como “Não informada” até a edição do pedido. Um pedido
histórico também está sem preço e aparece como “A definir”. Os produtos
`PRE001` (insumo `FITCET` ausente) e `KIT001` (sem composição) precisam de revisão;
seu custo e preço sugerido não são exibidos como números incompletos. A edição
de pedidos antigos exige definir uma data de entrega e um preço para cada item.

O total da tela inicial soma somente pedidos com todos os preços definidos.
O relatório segue esse mesmo critério para o total, o ticket médio e a lista de
itens vendidos.
“Média vendida” só aparece para produtos escolhidos do cadastro nos pedidos;
itens avulsos não são associados automaticamente ao produto por semelhança do nome.

Na aba **Relatórios**, escolha um mês e ano para filtrar pela **data de cadastro
do pedido**, ou **Total** para todo o histórico. Os pedidos importados da planilha
não tinham data de cadastro; por isso entram no Total, mas não nos meses.

O estoque começa com saldo **zero** porque a planilha não informa quantas
embalagens foram compradas ou ainda estão disponíveis. Antes de produzir,
registre o estoque inicial em **Entrada** ou **Ajustar saldo**, na mesma unidade
usada na receita. Pedidos anteriores a esta atualização não são abatidos de
forma retroativa. O saldo pode ficar negativo para mostrar faltas ou lançamentos
pendentes. Alterações posteriores na composição de um produto não mudam as
retiradas já registradas; uma edição nos itens do pedido estorna o consumo
anterior e aplica a composição atual.

Ao cadastrar cores em um insumo que já tinha estoque, o saldo anterior continua
visível em **Sem variação (legado)**; ele não é distribuído automaticamente entre
as cores. Use **Transferir** para atribuí-lo. Remover uma cor do cadastro a
inativa para novos pedidos, mas mantém seu saldo e histórico para consulta ou
ajuste. Pedidos já registrados preservam a cor escolhida.

O comprovante em PDF é um resumo do pedido e não é nota fiscal. Os dados ficam
apenas no computador; para transferi-los, copie ou restaure `marte.db` com o
aplicativo fechado.

## Melhorias de cadastro

- Insumos: filtros combináveis por nome/código, tamanho, gramatura, variação e
  estado, com botão Limpar. O campo Data do preço (DD/MM/AAAA) é editável e
  aparece na listagem. Cadastros antigos ficam com data não informada até edição.
  Em cadastros novos, a data sugerida é hoje; atualize-a ao revisar o preço.
- Produtos: código manual obrigatório e único. Na composição, digite parte do
  nome ou código do insumo e abra a lista para selecionar o resultado.
- Novo insumo na composição: abre o cadastro sem perder o produto em edição;
  ao salvar, o insumo fica selecionado. Informe a quantidade e clique Adicionar.

Estas alterações de código não acionam a compilação automaticamente. Para
compilar no computador, baixe o código atualizado e execute
`compilar_windows.bat`. Para publicar uma atualização, configure antes uma
versão superior à última Release com `configurar_release.py`.

## Build 2.1.0 — compras e resultado mensal

A aba Compras registra compras já recebidas e pagas de **insumos cadastrados**.
Produtos acabados continuam sendo compostos por esses insumos. Informe fornecedor
(opcional), insumo/variação, quantidade na unidade do cadastro e total pago pela
linha. Ex.: duas embalagens de 100 folhas = 200 un. A data é a data atual.
Confira os itens antes de confirmar: compras confirmadas ficam disponíveis para
consulta e não são editadas ou excluídas nesta versão.

A confirmação salva a compra, dá entrada na variação e atualiza o preço e a data
do insumo em uma transação única. Preço da embalagem = total pago ÷ quantidade
comprada × quantidade por embalagem cadastrada. Se o mesmo insumo aparece em
várias linhas/cores, o preço é calculado sobre os totais da compra, igual para
as cores. Os custos e preços sugeridos dos produtos passam a usar o novo custo;
os preços dos pedidos já gravados continuam os valores originais.

Relatórios mostram vendas, compras pagas, saldo comercial e resultado positivo,
negativo ou equilibrado por mês, inclusive no PDF. Vendas usam o mês de cadastro
do pedido, excluindo presentes e pedidos sem preço; não são recebimentos por
data de pagamento. Compras usam a data do registro. Não há outras despesas,
tributos ou histórico completo de recebimentos: o saldo não é lucro líquido nem
fluxo de caixa. Compras anteriores não registradas não entram no relatório.

Estoque parado significa saldo positivo atual dos insumos/variações, incluindo
inativos, ao custo cadastrado mais recente. Saldos negativos não reduzem esse
valor. Não é avaliação histórica do mês nem classificação por tempo sem venda.

Para compilar: baixe a branch main e execute `compilar_windows.bat`. A configuração
do atualizador já está preparada com a versão 2.1.0 e o endereço deste repositório.
Não é necessário alterar release-version.txt para compilar localmente; alterá-lo
aciona o GitHub Actions. Esta entrega não publica uma Release automaticamente.

## Build 2.1.1 — janela e identidade visual

O ERP abre maximizado, mantendo os controles de fechar e a barra do Windows.
F11 alterna tela cheia e Esc sai dela. Em telas menores, barras de rolagem
mantêm o menu e a área de trabalho acessíveis; o rodapé do produto tem espaço
reservado para salvar. Janelas de cadastro respeitam o tamanho da tela.

O tema usa bordô #7A2E3A, verde botânico #55613F, dourado #C79A5A,
pergaminho #F6F1E8, bege #D8B08C e marrom #3A2417. Títulos usam
Cormorant Garamond/Garamond quando instaladas, com alternativa Georgia;
textos usam Libre Franklin/Montserrat, com alternativa Segoe UI. Nenhuma
fonte precisa ser baixada para usar o ERP offline.

Compile com compilar_windows.bat. A versão do atualizador está em 2.1.1.

## Build 2.2.0 — rendimento do produto base e tabelas

Todas as tabelas têm linhas alternadas, destaque dourado sob o mouse e seleção
bordô com texto branco. Alertas de estoque negativo continuam visíveis.

No produto, informe quantas unidades a composição do produto base produz.
Exemplo: 1 folha + os demais materiais para fabricar 5 chaveiros → rendimento 5.
Cadastre as quantidades de TODOS os insumos para essas 5 peças. O custo da
composição é dividido por 5 para obter o custo unitário e o preço sugerido.
O preço de tabela também é por peça. No pedido, informe o total de peças:
1 consome 0,2 da receita; 5 consomem 1 receita; 10 consomem 2 receitas.
A baixa preserva a cor/variação escolhida. Não arredonda folhas para cima.

Cadastros anteriores recebem rendimento 1; só altere o rendimento depois de
conferir se a composição representa o lote inteiro. Se o preço de tabela antigo
era de um kit, ajuste-o para o preço por peça. Vender um kit de 5 corresponde a
quantidade 5 no pedido; não há cadastro separado de tamanhos de kit nesta versão.

Alterar o rendimento não altera pedidos ou estoque já movimentado. Editar
somente pagamento/entrega preserva a baixa anterior. Ao mudar os itens ou as
quantidades de um pedido, o ERP estorna a baixa anterior e aplica a composição
e o rendimento atuais. Excluir o pedido estorna a quantidade efetivamente baixada.

Compile com compilar_windows.bat. Versão preparada: 2.2.0.

## Build 2.3.0 — acabamentos no pedido

Ao abrir o ERP pela primeira vez nesta versão, são criados os insumos BOPP
Brilhante 30μ, Fosco Anti-risco 30μ e Holográfico 30μ, por folha A4. Os preços
começam não configurados (zero); o orçamento com acabamento exige custo positivo.
Em **Insumos → Acabamentos**, vincule um insumo diferente a cada acabamento.
Se as receitas antigas já usam um BOPP genérico, vincule esse insumo ao Brilhante
para reconhecê-lo como padrão sem modificar as receitas existentes.

Informe o total pago pelo rolo/embalagem e quantas folhas A4 úteis ele rende.
Um rolo de 50 m não determina sozinho o número de folhas: largura e perdas
precisam ser consideradas. O custo por A4 é valor da embalagem dividido pelo
rendimento em folhas. Esse rendimento da embalagem é independente do rendimento
do produto base. A configuração não altera saldos; registre entradas em Compras
ou Estoque.

Os adicionais iniciais por peça são R$ 0,00 (Brilhante), R$ 3,00 (Fosco) e
R$ 5,00 (Holográfico), editáveis nessa tela. Brilhante mantém adicional zero.
Na composição do produto use somente o BOPP padrão. O acabamento escolhido
fica no item do pedido; a receita original permanece inalterada.

O cálculo é: substituir o custo do BOPP na proporção utilizada, dividir a
composição pelo rendimento, aplicar o multiplicador e somar o adicional por
peça. Para produtos laminados, essa fórmula define a sugestão no pedido mesmo
quando existe preço de tabela. O operador pode ajustar o preço de venda; a
margem bruta exibida considera esse preço. Margem = (venda − custo) ÷ venda.
Custo e acabamento ficam registrados no item; mudanças de preço posteriores
não recalculam itens antigos. O botão Acabamento permite recalcular um item
selecionado. A baixa usa o BOPP escolhido e a exclusão estorna o material usado.

O resumo do produto mostra quatro linhas: custo do produto base, rendimento,
custo por unidade e preço sugerido. O banco armazena os custos base/unitário,
rendimento, multiplicador e sugerido, mantendo os campos calculados atualizados
por gatilhos quando composição, rendimento ou preço dos insumos mudam.
Exemplo: R$ 13,64 ÷ 5 = R$ 2,728 → exibido R$ 2,73; × 1,8 → R$ 4,91.
Não se arredonda o custo antes de multiplicar. Tamanhos comerciais de kits
não foram criados; a quantidade no pedido continua sendo o número de peças.

Insumos inativos ficam ocultos por padrão. Para desarquivar, filtre Estado por
Inativo e use Ativar / inativar. Clicar no cabeçalho de qualquer tabela alterna
ordem crescente/decrescente, mantendo as linhas alternadas.

Compile a versão 2.3.0 com compilar_windows.bat. Nenhuma Release é publicada
automaticamente por estas alterações.

## Build 2.4.0 — produtos por variação, kits, clientes e CSV

Esta versão substitui a seção **Acabamento do item** por versões no cadastro de produtos. Os campos antigos permanecem no banco para preservar pedidos e PDFs históricos, mas não há seleção de acabamento em novos pedidos.

### Insumos e opções

- Categorias: **Produção** e **Embalagem**. Cadastros existentes começam em Produção; altere a categoria das embalagens.
- Cada insumo tem uma lista expansível de **Opção → Variação**. Exemplo: `Wire-o 3/4 → Dourado` e `Wire-o 1/2 → Preto`. Não há limite de cinco linhas.
- Cada variação pode ter seu próprio **valor da embalagem**. Em branco, usa o preço padrão do insumo. O divisor continua sendo a quantidade por embalagem/rolo.
- O custo de um insumo sem variação definida é o maior entre as variações ativas. Ao fixar uma variação, vale seu preço específico.
- Renomear uma opção mantém seu identificador e o histórico de estoque. Remover uma linha a inativa, sem apagar os movimentos anteriores.
- Compras de variações com preço próprio atualizam somente esse preço; cores com preço compartilhado continuam seguindo o preço comum do insumo.

### Produtos e composição

- Duas listas de seleção: insumos de Produção e insumos de Embalagem. Cada seção tem sua árvore, quantidade, unidade, quantidade de folhas e custo.
- Para trocar o BOPP, selecione um produto e use **Criar variação**. Informe código e identificação próprios, remova o BOPP antigo da cópia e adicione o novo. A composição do produto original não muda.
- Opções de insumos com preços diferentes geram versões separadas ao salvar o produto. Essas versões têm código, composição, custo e estoque próprios. O produto base usa o maior custo quando a opção está indefinida. Variações já geradas são independentes: editar a composição do produto base não sobrescreve suas receitas.
- As combinações são geradas para as opções de custo; a interface aceita mais de cinco opções. Para evitar criação acidental de milhares de produtos, há limite de 1.000 combinações por operação, com erro antes de gravar.
- A tabela agrupa versões em árvore e apresenta a SOMA dos custos unitários e dos custos dos lotes dos produtos visíveis. Essas somas não representam valor de estoque.
- A coluna **Folhas/lote** soma quantidades cuja unidade contém `folha` ou é `A4`. Use essas unidades para papéis e filmes medidos por folha.
- Filtros de Insumos, Produtos, Clientes e Pedidos começam recolhidos e podem ser abertos pelo botão **Mostrar filtros**.

### Rendimento, custo mínimo e kits

O cadastro pergunta quantas peças a composição informada produz e quais quantidades são vendidas em kits, por exemplo `1, 6, 12, 50`. No pedido, selecionar um kit preenche a quantidade de peças; também é possível digitar outra quantidade inteira.

Para a origem **Produzir**:

```
lotes = teto(quantidade_pedida / rendimento)
custo_total = custo_da_composição × lotes
custo_por_peça_do_pedido = custo_total / quantidade_pedida
preço_sugerido_por_peça = arredondar(custo_total × multiplicador / quantidade_pedida)
```

Se houver preço mínimo por peça, a sugestão usa o maior entre ele e o cálculo acima. O preço pode ser alterado manualmente no pedido, com recálculo da margem. O arredondamento do preço unitário em centavos pode gerar diferença de alguns centavos no total de kits.

Exemplo: composição de R$ 6,00 rende 6 marca-páginas, multiplicador 2:

| Pedido | Lotes | Custo total | Venda sugerida total | Sobra em estoque |
|---|---:|---:|---:|---:|
| 1 peça | 1 | R$ 6,00 | R$ 12,00 | 5 |
| 6 peças | 1 | R$ 6,00 | R$ 12,00 | 0 |
| 12 peças | 2 | R$ 12,00 | R$ 24,00 | 0 |

O estoque é movimentado ao salvar o pedido, como nas versões anteriores. A origem Produzir desconta os insumos para lotes completos e registra as sobras como produtos prontos. Se a produção ainda não foi realizada fisicamente, os saldos representam a movimentação prevista do pedido cadastrado.

### Estoque de produtos

A aba Estoque apresenta uma seção de produtos prontos, com saldo, valor parado, entrada, retirada, ajuste e histórico. Na origem **Estoque pronto**, o pedido retira somente produtos; não desconta insumos novamente. A venda é bloqueada se não houver saldo suficiente.

Editar ou excluir um pedido estorna os movimentos correspondentes. Uma produção cuja sobra já foi retirada por outro pedido não pode ser excluída antes de estornar essa retirada. Pedidos antigos mantêm o modelo de consumo anterior e os preços históricos; a migração não lança uma nova baixa para eles.

O valor de estoque parado do relatório passa a incluir insumos e produtos prontos, calculados pelos custos atuais. Não é um cálculo de valor de mercado ou de recebimentos.

### Clientes

Nova aba **Clientes**, com nome, telefone, e-mail, data de nascimento e endereço. No pedido, selecione um cliente ou use `+` para cadastrar. Ao salvar sem cliente selecionado, o cadastro é aberto. Pedidos antigos continuam com seu nome histórico; ao editar um deles sem vínculo, o cadastro pode ser criado a partir desse nome.

### Importação de produtos

Em Produtos, o ícone **⇩** ao lado de Ativar / inativar oferece **Importar CSV** e **Baixar modelo CSV**. O arquivo `modelo_produtos.csv` também está na raiz do repositório.

- Uma linha por produto; mantenha todos os cabeçalhos do modelo.
- Salve preferencialmente como CSV UTF-8 separado por ponto e vírgula. São aceitos CSV com vírgula e arquivos Windows-1252.
- `nome`, `codigo`, `rendimento`, `multiplicador`, `kits` e `insumos` são obrigatórios. Tamanho, gramatura, preço mínimo e variações fixas podem ficar vazios.
- `insumos`: `CODIGO_PAPEL=1|CODIGO_EMBALAGEM=6`. Os códigos precisam existir e estar ativos.
- `kits`: `1|6|12`.
- `variacoes`: opcional, por exemplo `WIR=Wire-o 3/4 · Dourado`. Use exatamente o rótulo cadastrado; o insumo deve pertencer à composição.
- Nome ou código duplicado, informação obrigatória ausente, quantidade inválida, insumo ou variação incompatível são sinalizados antes da importação.
- **Corrigir selecionado** altera só aquela linha da revisão. **Ignorar incompatíveis e importar** grava apenas linhas válidas. O aviso final informa `X produtos adicionados` (incluindo versões de custo geradas) e quantas linhas foram ignoradas.
- A linha de exemplo do modelo deve ser substituída pelos dados reais; seus códigos de insumos são ilustrativos.

### Compilar

Baixe o código atualizado completo e execute `compilar_windows.bat` no Windows. Os módulos `catalog_core.py` e `catalog_ui.py` são incluídos automaticamente pelo PyInstaller. A versão interna é **2.4.0**. Esta alteração de código não dispara uma compilação ou publicação de Release; `release-version.txt` permanece inalterado.

Validação automatizada: 53 testes, cobrindo migração, históricos, lotes, kits, preços de variações, estornos, saldo de produtos, clientes, compras e importação CSV. A interface e o EXE precisam de validação visual no Windows.
