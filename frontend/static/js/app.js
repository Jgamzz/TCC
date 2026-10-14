function estoqueInfo(qtd) {
    qtd = Number(qtd);
    if (qtd <= 5) return { color: '#dc2626', pct: Math.min(qtd, 100) };
    if (qtd <= 20) return { color: '#d97706', pct: Math.min(qtd, 100) };
    return { color: '#16a34a', pct: Math.min(qtd, 100) };
}
function validadeInfo(dateStr) {
    if (!dateStr) return { label: 'Válido', cls: 'valido' };
    const diff = (new Date(dateStr) - new Date()) / 86400000;
    if (diff < 0) return { label: 'Vencido', cls: 'vencido' };
    if (diff <= 7) return { label: 'Alerta', cls: 'alerta' };
    return { label: 'Válido', cls: 'valido' };
}
function margem(p) {
    return p.custo > 0 ? ((p.preco_atual - p.custo) / p.custo) * 100 : 0;
}

function buildNav() {
  const items = [
    {id:'inicio', icon:'🏠', label:'Início'},
    {id:'gestao', icon:'📊', label:'Gestão', roles:[CARGO_GER,CARGO_DONO]},
    {id:'produtos', icon:'📦', label:'Produtos'},
    {id:'estoque', icon:'🗄️', label:'Estoque'},
    {id:'validade', icon:'📅', label:'Validade'},
    {id:'concorrencia', icon:'👥', label:'Concorrência'},
    {id:'equipa', icon:'👥', label:'Equipe', roles:[CARGO_DONO]},
    {id:'historico', icon:'📜', label:'Histórico', roles:[CARGO_GER,CARGO_DONO]},
    {id:'configuracoes', icon:'⚙️', label:'Configurações', roles:[CARGO_DONO]}
  ];
  const nav = document.getElementById('navBar');
  nav.innerHTML = items
    .filter((i) => !i.roles || i.roles.includes(user.Cargo_ID))
    .map(
      (i) =>
        `<button data-id="${i.id}" onclick="goTo('${i.id}')" title="${i.label}"><span class="nav-icon">${i.icon}</span><span class="nav-label">${i.label}</span></button>`,
    )
    .join('');
  markActive();
}

function markActive() {
  document
    .querySelectorAll('#navBar button')
    .forEach((b) => b.classList.toggle('active', b.dataset.id === currentPage));
}
function goTo(id) {
  currentPage = id;
  markActive();
  render();
}

const SIDEBAR_STATE_KEY = 'sgb_varejo_sidebar_collapsed';

function atualizarBotaoSidebar() {
  const app = document.getElementById('app');
  const button = document.getElementById('sidebarToggle');
  if (!app || !button) return;
  const recolhida = app.classList.contains('sidebar-collapsed');
  button.textContent = recolhida ? '☰' : '×';
  button.setAttribute('aria-label', recolhida ? 'Expandir menu' : 'Recolher menu');
  button.title = recolhida ? 'Expandir menu' : 'Recolher menu';
}

function alternarSidebar() {
  const app = document.getElementById('app');
  if (!app) return;
  const recolhida = app.classList.toggle('sidebar-collapsed');
  localStorage.setItem(SIDEBAR_STATE_KEY, recolhida ? 'true' : 'false');
  atualizarBotaoSidebar();
}

function restaurarSidebar() {
  if (localStorage.getItem(SIDEBAR_STATE_KEY) === 'true') {
    document.getElementById('app').classList.add('sidebar-collapsed');
  }
  atualizarBotaoSidebar();
}

async function render() {
  const main = document.getElementById('mainView');
  if (currentPage === 'gestao') { await renderGestao(); return; }
  if (currentPage === 'concorrencia') { await renderConcorrenciaPlanilhas(); return; }
  if (currentPage === 'historico') { await renderHistorico(); return; }
  
  if (currentPage === 'equipa' && usuarios.length === 0) {
    await refreshUsuarios();
  }

  const titles = {
    inicio:'Painel de Controle',
    produtos:'Produtos',
    estoque:'Estoque',
    validade:'Validade',
    concorrencia:'Monitoramento da Concorrência',
    equipa:'Gestão de Equipe',
    historico:'Histórico e Relatórios',
    configuracoes:'Configurações do Sistema'
  };
  main.innerHTML = renderDashboard(titles[currentPage] || 'Dashboard');

  if (currentPage === 'configuracoes') carregarConfiguracoesLocais();
  
  if (currentPage === 'inicio') initDashboardCharts();
}

function renderDashboard(title) {
  const canEdit = user.Cargo_ID === CARGO_GER || user.Cargo_ID === CARGO_DONO;
  const isDono = user.Cargo_ID === CARGO_DONO;
  let list = produtos.slice();

  if (currentPage === 'configuracoes') {
    return `
      <h1>${title} - ${user.Cargo_Name} ${user.Name}</h1>
      <div class="cards settings-grid">
        <div class="card settings-card">
          <h2 style="font-size:18px; margin-top:0; margin-bottom: 20px; border-bottom: 1px solid var(--borda); padding-bottom: 10px;">Travas de Segurança e Motor de Regras</h2>

          <label style="display:block; font-size:14px; font-weight:600; color:var(--texto); margin-bottom:8px;">Margem Mínima de Lucro (%)</label>
          <div class="note" style="margin-bottom:12px; font-size:12px;">O sistema bloqueará sugestões de desconto que resultem numa margem de lucro inferior a este valor.</div>
          <input type="number" id="cfg_margem" class="modal-input" min="0" max="100" step="0.1" placeholder="Ex: 15">

          <label style="display:block; font-size:14px; font-weight:600; color:var(--texto); margin-bottom:8px;">Dias de Validade para Alerta</label>
          <div class="note" style="margin-bottom:12px; font-size:12px;">Produtos que vençam num prazo igual ou inferior a este (em dias) receberão sugestão automática de desconto.</div>
          <input type="number" id="cfg_dias_validade" class="modal-input" min="1" step="1" placeholder="Ex: 7">

          <label style="display:block; font-size:14px; font-weight:600; color:var(--texto); margin-bottom:8px;">Limiar de Giro Baixo (Unidades/30 dias)</label>
          <div class="note" style="margin-bottom:12px; font-size:12px;">Se as vendas nos últimos 30 dias forem inferiores a este valor, o sistema sugerirá descontos progressivos.</div>
          <input type="number" id="cfg_limiar_giro" class="modal-input" min="0" step="1" placeholder="Ex: 10">

          <button class="btn btn-verde settings-save" onclick="salvarConfiguracoes()">Salvar Configurações</button>
        </div>
      </div>
    `;
  }

  if (currentPage === 'inicio') {
    let valorTotalCusto = 0, valorTotalPreco = 0, totalAlertas = 0, somaMargens = 0, produtosComMargem = 0;
    list.forEach(p => {
      valorTotalCusto += (p.custo * p.estoque);
      valorTotalPreco += (p.preco_atual * p.estoque);
      if (p.custo > 0) { somaMargens += margem(p); produtosComMargem++; }
      if (estoqueInfo(p.estoque).color !== '#16a34a' || validadeInfo(p.data_validade).cls !== 'valido') totalAlertas++;
    });
    const margemMedia = produtosComMargem > 0 ? (somaMargens / produtosComMargem).toFixed(1) : 0;
    const top5Margem = list.slice().sort((a, b) => margem(b) - margem(a)).slice(0, 5);
    
    return `
      <h1>${title}</h1>
      <div class="cards" style="grid-template-columns: repeat(4, 1fr);">
        <div class="card"><div class="lbl">Custo em Estoque</div><div class="val">R$ ${valorTotalCusto.toFixed(2)}</div></div>
        <div class="card"><div class="lbl">Potencial de Venda</div><div class="val" style="color:#15803d;">R$ ${valorTotalPreco.toFixed(2)}</div></div>
        <div class="card"><div class="lbl">Margem Média</div><div class="val" style="color:var(--azul-escuro);">${margemMedia}%</div></div>
        <div class="card alert" style="cursor:pointer;" onclick="goTo('estoque')"><div class="lbl">Atenção (Stock/Validade)</div><div class="val">${totalAlertas} item(ns)</div></div>
      </div>

      <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 20px; margin-top: 28px;">
        <div>
          <h2 style="font-size:16px; border-bottom:1px solid var(--borda); padding-bottom:8px; margin-top:0;">Top 5 Produtos (Maior Margem)</h2>
          <table>
            <thead><tr><th>Produto</th><th>Custo</th><th>Preço</th><th>Margem</th></tr></thead>
            <tbody>
              ${top5Margem.map(p => `
                <tr>
                  <td>${p.nome}</td>
                  <td>R$ ${p.custo.toFixed(2)}</td>
                  <td>R$ ${p.preco_atual.toFixed(2)}</td>
                  <td style="color:var(--azul-escuro); font-weight:bold;">${margem(p).toFixed(1)}%</td>
                </tr>
              `).join('') || `<tr><td colspan="4" style="text-align:center;" class="muted">Sem dados</td></tr>`}
            </tbody>
          </table>
        </div>
        
        <div>
          <h2 style="font-size:16px; border-bottom:1px solid var(--borda); padding-bottom:8px; margin-top:0;">Saúde do Estoque</h2>
          <div style="background:#fff; border:1px solid var(--borda); border-radius:8px; padding:16px; height: 260px; display:flex; justify-content:center;">
            <canvas id="estoqueChart"></canvas>
          </div>
        </div>

        <div>
          <h2 style="font-size:16px; border-bottom:1px solid var(--borda); padding-bottom:8px; margin-top:0;">Capital Empatado (Top 5)</h2>
          <div style="background:#fff; border:1px solid var(--borda); border-radius:8px; padding:16px; height: 260px; display:flex; justify-content:center;">
            <canvas id="capitalChart"></canvas>
          </div>
        </div>
      </div>
    `;
  }

  let thead = '', tbody = '';
  if (currentPage === 'produtos') {
    thead = `<tr><th>Produto</th><th>Custo</th><th>Preço Atual</th><th>Ações</th></tr>`;
    tbody = list.map(p => `<tr>
      <td>${p.nome}</td>
      <td>R$ ${p.custo.toFixed(2)}</td>
      <td>R$ ${p.preco_atual.toFixed(2)}</td>
      <td>
        ${canEdit ? `<button class="btn btn-azul" onclick="openProdutoModal(${p.id_produto})">Alterar</button>` : ''}
        <button class="btn" style="background:var(--laranja);color:#fff;margin-left:6px;" onclick="abrirModalFeedback(${p.id_produto})">💬 Feedback</button>
        ${isDono ? `<button class="btn btn-vermelho" style="margin-left:6px" onclick="deleteProduto(${p.id_produto})">Excluir</button>` : ''}
      </td>
    </tr>`).join('');
  } else if (currentPage === 'estoque') {
    list.sort((a, b) => a.estoque - b.estoque);
    thead = `<tr><th>Produto</th><th>Estoque Atual</th><th>Status</th><th>Ações Rápidas</th></tr>`;
    tbody = list.map(p => {
      const est = estoqueInfo(p.estoque);
      return `<tr><td>${p.nome}</td><td><div class="bar"><div style="width:${est.pct}%;background:${est.color}"></div></div><div class="qty">${p.estoque} un.</div></td>
        <td style="color:${est.color}; font-weight:600;">${p.estoque <= 5 ? 'Crítico' : p.estoque <= 20 ? 'Baixo' : 'Saudável'}</td>
        <td><button class="btn btn-verde" onclick="abrirMovimentacaoRapida(${p.id_produto}, 'VENDA')">Registrar Movimentação</button></td></tr>`;
    }).join('');
  } else if (currentPage === 'validade') {
    list.sort((a, b) => validadeInfo(a.data_validade).cls === 'valido' ? 1 : -1);
    thead = `<tr><th>Produto</th><th>Data de Validade</th><th>Situação</th><th>Ação do Sistema</th></tr>`;
    tbody = list.map(p => {
      const val = validadeInfo(p.data_validade);
      const btnPromocao = (val.cls !== 'valido' && canEdit) ? `<button class="btn" style="background:var(--laranja);color:#fff;" onclick="pedirSugestaoDesconto(${p.id_produto})">Analisar Desconto</button>` : '—';
      return `<tr><td>${p.nome}</td><td>${p.data_validade ? new Date(p.data_validade).toLocaleDateString('pt-BR') : 'Sem validade'}</td>
        <td><span class="badge ${val.cls}">${val.label}</span></td><td>${btnPromocao}</td></tr>`;
    }).join('');
  } else if (currentPage === 'concorrencia') {
    thead = `<tr><th>Produto</th><th>Custo</th><th>Nosso Preço</th><th>Ações</th></tr>`;
    tbody = list.map(p => `<tr><td>${p.nome}</td><td>R$ ${p.custo.toFixed(2)}</td><td>R$ ${p.preco_atual.toFixed(2)}</td>
      <td><button class="btn btn-azul" onclick="abrirModalConcorrencia(${p.id_produto})">Atualizar Concorrente</button></td></tr>`).join('');
  } else if (currentPage === 'equipa') {
    thead = `<tr><th>Nome</th><th>Login</th><th>Cargo</th><th>Status</th><th>Ações</th></tr>`;
    tbody = usuarios.map(u => `<tr>
      <td>${u.Name}</td>
      <td>${u.Username}</td>
      <td>${u.Cargo_Name}</td>
      <td><span class="badge ${u.Is_Active ? 'valido' : 'vencido'}">${u.Is_Active ? 'Ativo' : 'Inativo'}</span></td>
      <td>
        <button class="btn btn-azul" onclick="openUsuarioModal(${u.ID})">Alterar</button>
        ${u.ID !== user.ID ? `<button class="btn btn-vermelho" style="margin-left:6px" onclick="deleteUsuario(${u.ID})">Excluir</button>` : ''}
      </td>
    </tr>`).join('');
  }

  if (!tbody) tbody = `<tr><td colspan="4" class="muted" style="text-align:center;">Nenhum dado para exibir.</td></tr>`;
    return `<h1>${title} - ${user.Cargo_Name} ${user.Name}</h1>
      ${(isDono && currentPage === 'produtos') ? `<div class="toolbar"><button class="btn btn-azul" onclick="openProdutoModal(null)">Registrar novo produto</button></div>` : ''}
      ${(isDono && currentPage === 'equipa') ? `<div class="toolbar"><button class="btn btn-azul" onclick="openUsuarioModal(null)">Adicionar Membro</button></div>` : ''}
      <table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
}

function initDashboardCharts() {
  // --- GRÁFICO 1: Saúde do Estoque (Doughnut Melhorado) ---
  const ctxEstoque = document.getElementById('estoqueChart');
  if (ctxEstoque) {
    let critico = 0, baixo = 0, saudavel = 0;
    produtos.forEach(p => {
      if (p.estoque <= 5) critico++;
      else if (p.estoque <= 20) baixo++;
      else saudavel++;
    });

    new Chart(ctxEstoque, {
      type: 'doughnut',
      data: {
        labels: ['Crítico', 'Baixo', 'Saudável'],
        datasets: [{
          data: [critico, baixo, saudavel],
          backgroundColor: ['#dc2626', '#d97706', '#16a34a'],
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { 
            position: 'bottom',
            labels: { boxWidth: 12, font: { size: 11 } }
          }
        }
      }
    });
  }

  // --- GRÁFICO 2: Capital Empatado (Gráfico de Barras) ---
  const ctxCapital = document.getElementById('capitalChart');
  if (ctxCapital) {
    const topCapital = produtos.slice()
      .sort((a, b) => (b.custo * b.estoque) - (a.custo * a.estoque))
      .slice(0, 5);

    new Chart(ctxCapital, {
      type: 'bar',
      data: {
        labels: topCapital.map(p => p.nome.length > 12 ? p.nome.substring(0, 10) + '...' : p.nome),
        datasets: [{
          label: 'Valor (R$)',
          data: topCapital.map(p => p.custo * p.estoque),
          backgroundColor: '#2f6fed',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { 
            beginAtZero: true,
            ticks: { font: { size: 10 } }
          },
          x: {
            ticks: { font: { size: 10 } }
          }
        }
      }
    });
  }
}

function initDashboardCharts() {
  // --- GRÁFICO 1: Saúde do Estoque (Doughnut Melhorado) ---
  const ctxEstoque = document.getElementById('estoqueChart');
  if (ctxEstoque) {
    let critico = 0, baixo = 0, saudavel = 0;
    produtos.forEach(p => {
      if (p.estoque <= 5) critico++;
      else if (p.estoque <= 20) baixo++;
      else saudavel++;
    });

    new Chart(ctxEstoque, {
      type: 'doughnut',
      data: {
        labels: ['Crítico', 'Baixo', 'Saudável'],
        datasets: [{
          data: [critico, baixo, saudavel],
          backgroundColor: ['#dc2626', '#d97706', '#16a34a'],
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { 
            position: 'bottom',
            labels: { boxWidth: 12, font: { size: 11 } }
          }
        }
      }
    });
  }

  // --- GRÁFICO 2: Capital Empatado (Gráfico de Barras) ---
  const ctxCapital = document.getElementById('capitalChart');
  if (ctxCapital) {
    const topCapital = produtos.slice()
      .sort((a, b) => (b.custo * b.estoque) - (a.custo * a.estoque))
      .slice(0, 5);

    new Chart(ctxCapital, {
      type: 'bar',
      data: {
        labels: topCapital.map(p => p.nome.length > 12 ? p.nome.substring(0, 10) + '...' : p.nome),
        datasets: [{
          label: 'Valor (R$)',
          data: topCapital.map(p => p.custo * p.estoque),
          backgroundColor: '#2f6fed',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { font: { size: 10 } }
          },
          x: {
            ticks: { font: { size: 10 } }
          }
        }
      }
    });
  }
}

async function renderGestao() {
  const main = document.getElementById('mainView');
  main.innerHTML = '<h1>Aprovação de Sugestões de Preço</h1><p>Carregando...</p>';
  try {
    const sugestoes = await api('/sugestoes');
    const rows = sugestoes.map((s) => {
      const p = produtos.find(prod => (prod.id || prod.id_produto) === s.id_produto);
      return `<tr><td>${p ? p.nome : 'Produto #' + s.id_produto}</td><td>R$ ${s.preco_atual.toFixed(2)}</td>
                <td style="color:var(--laranja);font-weight:600;">Para R$ ${s.preco_sugerido.toFixed(2)}</td><td>${s.motivo}</td>
                <td>
                  <button class="btn btn-verde" style="margin-bottom:4px;" onclick="decidirSugestao(${s.id_sugestao}, 'APROVADA')">Aceitar</button>
                  <button class="btn btn-azul" style="margin-bottom:4px;" onclick="abrirModalEditarSugestao(${s.id_sugestao}, ${s.preco_sugerido})">Editar</button>
                  <button class="btn btn-vermelho" onclick="decidirSugestao(${s.id_sugestao}, 'REJEITADA')">Rejeitar</button>
                </td></tr>`;
    }).join('') || '<tr><td colspan="5" class="muted" style="text-align:center;">Nenhuma sugestão pendente.</td></tr>';
    main.innerHTML = `<h1>Aprovação de Sugestões de Preço</h1><table><thead><tr><th>Produto</th><th>Preço Atual</th><th>Sugestão</th><th>Justificativa</th><th>Ações</th></tr></thead><tbody>${rows}</tbody></table>`;
  } catch (e) {
    main.innerHTML = `<h1>Erro</h1><div class="err">${e.message}</div>`;
  }
}

function escaparHtml(valor) {
  return String(valor).replace(/[&<>"']/g, (caractere) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[caractere]);
}

async function renderHistorico() {
  const main = document.getElementById('mainView');
  main.innerHTML = '<h1>Histórico e Relatórios</h1><p>Carregando histórico...</p>';

  try {
    const eventos = await api('/historico');
    if (eventos.length === 0) {
      main.innerHTML = `
        <h1>Histórico e Relatórios</h1>
        <div class="card empty-state">
          <span class="empty-state-icon">📋</span>
          <strong>Nenhum histórico disponível</strong>
          <span>Feedbacks, movimentações de estoque e alterações de preço aparecerão aqui.</span>
        </div>
      `;
      return;
    }

    const formatarData = (valor) =>
      new Date(valor).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
    const linhas = eventos.map((evento) => {
      let tipo;
      let detalhes;
      if (evento.tipo === 'FEEDBACK') {
        tipo = '<span class="history-badge history-feedback">Feedback</span>';
        detalhes = `${evento.cliente ? `<strong>Cliente:</strong> ${escaparHtml(evento.cliente)} — ` : ''}${escaparHtml(evento.mensagem)}`;
      } else if (evento.tipo === 'ESTOQUE') {
        const entrada = evento.tipo_operacao === 'ENTRADA';
        tipo = `<span class="history-badge ${entrada ? 'history-entrada' : 'history-saida'}">${entrada ? 'Entrada' : 'Saída'} de estoque</span>`;
        detalhes = `${escaparHtml(evento.quantidade)} unidade(s) — ${escaparHtml(evento.motivo)}`;
      } else {
        tipo = '<span class="history-badge history-preco">Alteração de preço</span>';
        detalhes = `De R$ ${escaparHtml(Number(evento.preco_antigo).toFixed(2))} para R$ ${escaparHtml(Number(evento.preco_novo).toFixed(2))} — ${escaparHtml(evento.motivo)}`;
      }
      return `<tr>
        <td>${escaparHtml(formatarData(evento.data))}</td>
        <td>${tipo}</td>
        <td>${escaparHtml(evento.produto)}</td>
        <td>${detalhes}</td>
      </tr>`;
    }).join('');

    main.innerHTML = `
      <h1>Histórico e Relatórios</h1>
      <div class="history-table-wrap">
        <table>
          <thead><tr><th>Data da movimentação</th><th>Tipo</th><th>Produto</th><th>Detalhes</th></tr></thead>
          <tbody>${linhas}</tbody>
        </table>
      </div>
    `;
  } catch (error) {
    main.innerHTML = `<h1>Histórico e Relatórios</h1><div class="err">${escaparHtml(error.message)}</div>`;
  }
}

async function renderConcorrenciaPlanilhas() {
  const main = document.getElementById('mainView');
  main.innerHTML = '<h1>Monitoramento da Concorrência</h1><p>Carregando preços...</p>';

  try {
    const comparacao = await api('/concorrentes/planilhas');
    if (comparacao.arquivos.length === 0) {
      main.innerHTML = `
        <h1>Monitoramento da Concorrência</h1>
        <div class="note">Nenhuma planilha encontrada. Coloque arquivos .xlsx ou .xlsm na pasta database/concorrentes e reinicie a aplicação.</div>
      `;
      return;
    }

    const formatarValor = (valor) =>
      new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
    const cabecalhos = comparacao.arquivos
      .map((arquivo) => `<th>${escaparHtml(arquivo.replace(/\.(xlsx|xlsm)$/i, ''))}</th>`)
      .join('');
    const linhas = comparacao.produtos.map((produto) => `
      <tr>
        <td>${escaparHtml(produto.nome_produto)}</td>
        ${comparacao.arquivos.map((arquivo) => {
          const precos = produto.precos[arquivo] || [];
          return `<td>${precos.length ? precos.map(formatarValor).join('<br>') : '—'}</td>`;
        }).join('')}
        <td>${produto.diferenca === null ? '—' : formatarValor(produto.diferenca)}</td>
      </tr>
    `).join('');

    main.innerHTML = `
      <h1>Monitoramento da Concorrência</h1>
      <div class="competitor-table-wrap">
        <table>
          <thead><tr><th>Produto</th>${cabecalhos}<th>Diferença de preços</th></tr></thead>
          <tbody>${linhas || `<tr><td colspan="${comparacao.arquivos.length + 2}" class="muted">As planilhas não contêm produtos.</td></tr>`}</tbody>
        </table>
      </div>
    `;
  } catch (error) {
    main.innerHTML = `<h1>Monitoramento da Concorrência</h1><div class="err">${escaparHtml(error.message)}</div>`;
  }
}

restaurarSidebar();
restaurarSessao();
