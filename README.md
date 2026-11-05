# SGPV

## Configuração segura

Configure as variáveis de ambiente antes de iniciar o sistema. Não grave credenciais no código nem em arquivos versionados:

- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- `JWT_SECRET_KEY`: chave aleatória longa e persistente; a aplicação não inicia sem ela.
- `INITIAL_ADMIN_NAME`, `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD`: usados somente para criar o primeiro Admin quando ainda não existe nenhum.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` e `APP_PUBLIC_URL`: necessários para envio de links de redefinição de senha.

O usuário inicial não é redefinido nem recriado a cada inicialização. Contas antigas com senha em texto são convertidas para hash com salt durante a migração automática. Após atualizar a aplicação, altere as credenciais iniciais que já tenham sido distribuídas.

No PowerShell, gere uma chave JWT com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Para desenvolvimento local, crie um arquivo `.env` na raiz do projeto com as variáveis necessárias, por exemplo:

```text
DB_USER=root
DB_PASSWORD=sua_senha_do_mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sgb_varejo
JWT_SECRET_KEY=gere_uma_chave_aleatoria
```

O `.env` é local e ignorado pelo Git. Variáveis de ambiente não vazias têm prioridade sobre os valores desse arquivo. Inicie com `.\.venv\Scripts\python.exe run.py`. `FLASK_DEBUG=1` deve ser usado somente em desenvolvimento. Em produção, defina as variáveis no ambiente do usuário/serviço que executará o servidor.

## Backup diário do MySQL

O script `scripts/backup_mysql.py` gera um dump consistente comprimido em `backups/`, mantém os últimos 30 dias e usa `MYSQLDUMP_BIN` ou `mysqldump` do `PATH`. Defina as variáveis `DB_*` no ambiente do usuário da tarefa agendada. `DB_BACKUP_DIR` pode apontar para um volume protegido e separado do servidor.

No Windows, registre a tarefa diária executando no PowerShell:

```powershell
.\scripts\install_backup_task.ps1
```

O agendador executará o backup diariamente às 01:00. Para verificar, execute a tarefa manualmente pelo Agendador de Tarefas e confirme a criação de um arquivo `.sql.gz`. Teste periodicamente a restauração em um banco isolado; não valide a restauração sobre a base de produção.

## Testes

Execute a suíte automatizada com:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O endpoint `/health` retorna `200` somente quando o processo consegue consultar o banco e pode ser usado por um monitor externo de disponibilidade.

## Giro de estoque e regras de precificação

O endpoint autenticado `GET /api/giro` informa, para cada produto ativo, a quantidade vendida nos últimos 7 e 30 dias corridos, além do saldo atual. O período é móvel a partir do momento da consulta. A geração de sugestões usa as vendas dos últimos 30 dias para comparar o giro com o limiar configurado.

A regra de validade aplica desconto quando a data do produto está entre hoje e antes do limite configurado (`dias_validade`); uma validade exatamente no limite não ativa essa regra, e produtos já vencidos não recebem desconto de validade. O aumento por giro alto só é aplicado quando existe preço de concorrente registrado e o preço atual está abaixo dele. Toda sugestão e aprovação respeita o piso `custo × (1 + margem_minima / 100)`.

Os testes verificam os períodos de 7/30 dias, os limites da regra de validade, a condição de comparação com concorrentes e o processamento de sugestões para 500 produtos. O teste de desempenho automatizado usa SQLite em memória; ele não substitui a medição de desempenho no ambiente MySQL de produção.

A formulação completa do motor, exemplos reproduzíveis, protocolo de comparação
com margem fixa e correção proposta para RF04/RF10 estão em
[`docs/metodologia_precificacao.md`](docs/metodologia_precificacao.md). O
projeto não contém dados experimentais suficientes para afirmar ganhos de lucro
ou redução de perdas; esses números só devem ser usados no artigo após uma
avaliação controlada.

## Reprodução do simulador

O simulador de Monte Carlo está em
[`scripts/simulador2.py`](scripts/simulador2.py). Ele usa um catálogo sintético
de 12 produtos declarado no próprio arquivo, que constitui a base de entrada
reproduzível da análise. O catálogo contém custos, preços, estoques, validades,
limiares de giro, margens mínimas, janelas de validade e preços concorrentes.

Para executar:

```powershell
py -m pip install -r requirements.txt
py .\scripts\simulador2.py
```

A simulação principal usa `semente=42`, 100 repetições e 30 dias. A análise de
sensibilidade reutiliza a mesma semente para as elasticidades `0.5` e `3.0`.
Esses parâmetros estão visíveis na chamada
`simular_monte_carlo(elasticidade=1.5)` e na definição do catálogo, permitindo
reproduzir os resultados sem dados externos.

Para a citação acadêmica, use a versão imutável publicada na tag
[`v1.0.0`](https://github.com/Jgamzz/TCC/tree/v1.0.0), e não uma branch em
desenvolvimento.
