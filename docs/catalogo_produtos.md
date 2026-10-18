# Catálogo portátil de produtos

O arquivo `database/produtos/produtos.xlsx` é o catálogo portátil dos produtos
próprios. Ele é criado automaticamente na primeira inicialização com os
produtos já cadastrados no banco.

Para cadastrar produtos em outra máquina, adicione linhas na planilha e copie
o arquivo junto com o projeto. Na inicialização seguinte, o sistema importa
somente produtos que ainda não existam, identificando-os pelo código ou pelo
nome. Produtos existentes e seus estoques não são sobrescritos; movimentações
continuam sendo registradas normalmente no banco.

As colunas obrigatórias são:

```text
nome,custo,preco_atual,estoque
```

Também podem ser informadas `codigo`, `descricao`, `categoria`, `fornecedor`,
`data_validade` no formato `AAAA-MM-DD` e `ativo` (`true`/`false`). Valores de
estoque preenchidos na planilha geram uma entrada inicial no histórico.