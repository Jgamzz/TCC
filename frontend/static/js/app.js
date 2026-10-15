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
const DISPLAY_MODE_KEY = 'sgb_varejo_display_mode';

function getDisplayMode() {
  return localStorage.getItem(DISPLAY_MODE_KEY) === 'list' ? 'list' : 'grid';
}

function collectionClass() {
  return `view-collection is-${getDisplayMode()}`;
}

function displayModeControl() {
  const mode = getDisplayMode();
  return `<div class="display-mode-control" role="group" aria-label="Modo de exibição">
    <span>Exibir:</span>
    <button type="button" data-display-mode="grid" class="btn btn-outline${mode === 'grid' ? ' selected' : ''}" aria-pressed="${mode === 'grid'}" onclick="setDisplayMode('grid')">Grade</button>
    <button type="button" data-display-mode="list" class="btn btn-outline${mode === 'list' ? ' selected' : ''}" aria-pressed="${mode === 'list'}" onclick="setDisplayMode('list')">Lista</button>
  </div>`;
}

function setDisplayMode(mode) {
  if (mode !== 'grid' && mode !== 'list') return;
  localStorage.setItem(DISPLAY_MODE_KEY, mode);
  document.querySelectorAll('.view-collection').forEach((collection) => {
    collection.classList.toggle('is-grid', mode === 'grid');
    collection.classList.toggle('is-list', mode === 'list');
  });
  document.querySelectorAll('.display-mode-control button').forEach((button) => {
    const selected = button.dataset.displayMode === mode;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
}

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

  if (currentPage === 'configuracoes') carregarConfiguracoesRemotas();
  
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
      ${displayModeControl()}
      <div class="${collectionClass()} cards dashboard-metrics">
        <div class="card"><div class="lbl">Custo em Estoque</div><div class="val">R$ ${valorTotalCusto.toFixed(2)}</div></div>
        <div class="card"><div class="lbl">Potencial de Venda</div><div class="val" style="color:#15803d;">R$ ${valorTotalPreco.toFixed(2)}</div></div>
        <div class="card"><div class="lbl">Margem Média</div><div class="val" style="color:var(--azul-escuro);">${margemMedia}%</div></div>
        <div class="card alert" style="cursor:pointer;" onclick="goTo('estoque')"><div class="lbl">Atenção (Stock/Validade)</div><div class="val">${totalAlertas} item(ns)</div></div>
      </div>

      <div class="${collectionClass()} dashboard-panels">
        <div>
          <h2 style="font-size:16px; border-bottom:1px solid var(--borda); padding-bottom:8px; margin-top:0;">Top 5 Produtos (Maior Margem)</h2>
          <div class="${collectionClass()} entity-grid">
            ${top5Margem.map(p => `
              <article class="entity-card">
                <h2>${escaparHtml(p.nome)}</h2>
                <dl class="entity-details">
                  <div><dt>Custo</dt><dd>R$ ${p.custo.toFixed(2)}</dd></div>
                  <div><dt>Preço atual</dt><dd>R$ ${p.preco_atual.toFixed(2)}</dd></div>
                  <div><dt>Margem</dt><dd class="suggested-price">${margem(p).toFixed(1)}%</dd></div>
                </dl>
              </article>
            `).join('') || `<p class="muted">Sem dados.</p>`}
          </div>
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

  let thead = '', tbody = '', cards = '';
  if (currentPage === 'produtos') {
    cards = list.map(p => `<article class="entity-card">
      <h2>${escaparHtml(p.nome)}</h2>
      <dl class="entity-details">
        <div><dt>Código</dt><dd>${escaparHtml(p.codigo || '—')}</dd></div>
        <div><dt>Categoria</dt><dd>${escaparHtml(p.categoria || '—')}</dd></div>
        <div><dt>Fornecedor</dt><dd>${escaparHtml(p.fornecedor || '—')}</dd></div>
        <div><dt>Custo</dt><dd>R$ ${p.custo.toFixed(2)}</dd></div>
        <div><dt>Preço atual</dt><dd>R$ ${p.preco_atual.toFixed(2)}</dd></div>
      </dl>
      <div class="entity-actions">
        ${canEdit ? `<button class="btn btn-azul" onclick="openProdutoModal(${p.id_produto})">Alterar</button>` : ''}
        <button class="btn btn-feedback" onclick="abrirModalFeedback(${p.id_produto})">Feedback</button>
        ${isDono ? `<button class="btn btn-vermelho" onclick="deleteProduto(${p.id_produto})">Excluir</button>` : ''}
      </div>
    </article>`).join('');
  } else if (currentPage === 'estoque') {
    list.sort((a, b) => a.estoque - b.estoque);
    cards = list.map(p => {
      const est = estoqueInfo(p.estoque);
      return `<article class="entity-card">
        <h2>${escaparHtml(p.nome)}</h2>
        <div class="stock-value">${p.estoque} <span>unidades</span></div>
        <div class="bar"><div style="width:${est.pct}%;background:${est.color}"></div></div>
        <p class="stock-status" style="color:${est.color}">${p.estoque <= 5 ? 'Crítico' : p.estoque <= 20 ? 'Baixo' : 'Saudável'}</p>
        ${canEdit ? `<button class="btn btn-verde" onclick="abrirMovimentacaoRapida(${p.id_produto})">Registrar movimentação</button>` : ''}
      </article>`;
    }).join('');
  } else if (currentPage === 'validade') {
    list.sort((a, b) => validadeInfo(a.data_validade).cls === 'valido' ? 1 : -1);
    cards = list.map(p => {
      const val = validadeInfo(p.data_validade);
      const btnPromocao = (val.cls !== 'valido' && canEdit) ? `<button class="btn btn-feedback" onclick="pedirSugestaoDesconto(${p.id_produto})">Analisar desconto</button>` : '';
      return `<article class="entity-card">
        <h2>${escaparHtml(p.nome)}</h2>
        <dl class="entity-details">
          <div><dt>Validade</dt><dd>${p.data_validade ? new Date(p.data_validade).toLocaleDateString('pt-BR') : 'Sem validade'}</dd></div>
          <div><dt>Situação</dt><dd><span class="badge ${val.cls}">${val.label}</span></dd></div>
          <div><dt>Estoque</dt><dd>${p.estoque} unidade(s)</dd></div>
        </dl>
        ${btnPromocao}
      </article>`;
    }).join('');
  } else if (currentPage === 'concorrencia') {
    cards = list.map(p => `<article class="entity-card">
      <h2>${escaparHtml(p.nome)}</h2>
      <dl class="entity-details">
        <div><dt>Custo</dt><dd>R$ ${p.custo.toFixed(2)}</dd></div>
        <div><dt>Nosso preço</dt><dd>R$ ${p.preco_atual.toFixed(2)}</dd></div>
      </dl>
      <button class="btn btn-azul" onclick="abrirModalConcorrencia(${p.id_produto})">Atualizar concorrente</button>
    </article>`).join('');
  } else if (currentPage === 'equipa') {
    thead = `<tr><th>Nome</th><th>Login</th><th>Cargo</th><th>Status</th><th>Ações</th></tr>`;
    tbody = usuarios.map(u => `<tr>
      <td data-label="Nome">${escaparHtml(u.Name)}</td>
      <td data-label="Login">${escaparHtml(u.Username)}</td>
      <td data-label="Cargo">${escaparHtml(u.Cargo_Name)}</td>
      <td data-label="Status"><span class="badge ${u.Is_Active ? 'valido' : 'vencido'}">${u.Is_Active ? 'Ativo' : 'Inativo'}</span></td>
      <td data-label="Ações">
        <button class="btn btn-azul" onclick="openUsuarioModal(${u.ID})">Alterar</button>
        ${u.ID !== user.ID ? `<button class="btn btn-vermelho" style="margin-left:6px" onclick="deleteUsuario(${u.ID})">Excluir</button>` : ''}
      </td>
    </tr>`).join('');
  }

  if (currentPage !== 'equipa') {
    return `<h1>${title} - ${escaparHtml(user.Cargo_Name)} ${escaparHtml(user.Name)}</h1>
      ${(currentPage === 'produtos') ? `<div class="toolbar product-filters">
        <input id="filtroNome" placeholder="Nome" aria-label="Filtrar por nome">
        <input id="filtroCodigo" placeholder="Código" aria-label="Filtrar por código">
        <input id="filtroCategoria" placeholder="Categoria" aria-label="Filtrar por categoria">
        <input id="filtroFornecedor" placeholder="Fornecedor" aria-label="Filtrar por fornecedor">
        <select id="filtroDisponivel" aria-label="Disponibilidade">
          <option value="">Todos</option><option value="true">Com estoque</option><option value="false">Sem estoque</option>
        </select>
        <button class="btn btn-azul" onclick="filtrarProdutos()">Filtrar</button>
      </div>` : ''}
      ${(isDono && currentPage === 'produtos') ? `<div class="toolbar"><button class="btn btn-azul" onclick="openProdutoModal(null)">Registrar novo produto</button></div>` : ''}
      ${currentPage !== 'configuracoes' ? displayModeControl() : ''}
      <section class="${collectionClass()} entity-grid">${cards || '<p class="muted">Nenhum dado para exibir.</p>'}</section>`;
  }
  if (!tbody) tbody = `<tr><td colspan="5" class="muted" style="text-align:center;">Nenhum dado para exibir.</td></tr>`;
  return `<h1>${title} - ${escaparHtml(user.Cargo_Name)} ${escaparHtml(user.Name)}</h1>
    <div class="toolbar"><button class="btn btn-azul" onclick="openUsuarioModal(null)">Adicionar membro</button></div>
    <table class="team-table"><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
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

async function filtrarProdutos() {
  const filtros = {
    nome: document.getElementById('filtroNome').value.trim(),
    codigo: document.getElementById('filtroCodigo').value.trim(),
    categoria: document.getElementById('filtroCategoria').value.trim(),
    fornecedor: document.getElementById('filtroFornecedor').value.trim(),
    disponivel: document.getElementById('filtroDisponivel').value
  };
  const query = new URLSearchParams(
    Object.entries(filtros).filter(([, valor]) => valor)
  );
  try {
    produtos = await api('/produtos/?' + query.toString());
    render();
  } catch (error) {
    showToast('Erro ao filtrar produtos: ' + error.message, 'error');
  }
}

async function renderGestao() {
  const main = document.getElementById('mainView');
  main.innerHTML = '<h1>Aprovação de Sugestões de Preço</h1><p>Carregando...</p>';
  try {
    const sugestoes = await api('/sugestoes');
    const cards = sugestoes.map((s) => {
      const p = produtos.find(prod => (prod.id || prod.id_produto) === s.id_produto);
      return `<article class="entity-card">
        <h2>${escaparHtml(p ? p.nome : 'Produto #' + s.id_produto)}</h2>
        <dl class="entity-details">
          <div><dt>Preço atual</dt><dd>R$ ${s.preco_atual.toFixed(2)}</dd></div>
          <div><dt>Preço sugerido</dt><dd class="suggested-price">R$ ${s.preco_sugerido.toFixed(2)}</dd></div>
        </dl>
        <p>${escaparHtml(s.motivo)}</p>
        <div class="entity-actions">
          <button class="btn btn-verde" onclick="decidirSugestao(${s.id_sugestao}, 'APROVADA')">Aceitar</button>
          <button class="btn btn-azul" onclick="abrirModalEditarSugestao(${s.id_sugestao}, ${s.preco_sugerido})">Editar</button>
          <button class="btn btn-vermelho" onclick="decidirSugestao(${s.id_sugestao}, 'REJEITADA')">Rejeitar</button>
        </div>
      </article>`;
    }).join('');
    main.innerHTML = `<h1>Aprovação de Sugestões de Preço</h1>
      <div class="toolbar"><button class="btn btn-azul" onclick="gerarSugestoesCatalogo()">Gerar sugestões para o catálogo</button></div>
      ${displayModeControl()}
      <section class="${collectionClass()} entity-grid">${cards || '<p class="muted">Nenhuma sugestão pendente.</p>'}</section>`;
  } catch (e) {
    main.innerHTML = `<h1>Erro</h1><div class="err">${escaparHtml(e.message)}</div>`;
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
    const relatorioHtml = `
      <section class="report-panel">
        <h2>Relatórios gerenciais</h2>
        <div class="report-filters">
          <select id="relatorioTipo" aria-label="Tipo de relatório">
            <option value="vendas">Vendas</option><option value="giro">Giro de estoque</option><option value="precos">Alterações de preço</option>
          </select>
          <label>De <input id="relatorioInicio" type="date"></label>
          <label>Até <input id="relatorioFim" type="date"></label>
          <button class="btn btn-azul" onclick="carregarRelatorio()">Gerar relatório</button>
        </div>
        <div id="relatorioResultado" aria-live="polite"></div>
      </section>`;
    const giroHtml = `
      <section class="report-panel">
        <h2>Giro de estoque por produto</h2>
        <p class="muted">Quantidade vendida em períodos móveis de 7 e 30 dias.</p>
        <div class="toolbar">
          <button class="btn btn-azul" type="button" onclick="carregarGiroEstoque()">Consultar giro semanal e mensal</button>
        </div>
        <div id="giroResultado" aria-live="polite"></div>
      </section>`;
    if (eventos.length === 0) {
      main.innerHTML = `
        <h1>Histórico e Relatórios</h1>
        ${displayModeControl()}
        ${relatorioHtml}
        ${giroHtml}
        <div class="card empty-state">
          <span class="empty-state-icon">📋</span>
          <strong>Nenhum histórico disponível</strong>
          <span>Cadastros, vendas, movimentações, preços, sugestões e demais ações realizadas no sistema aparecerão aqui com data e horário.</span>
        </div>
      `;
      definirPeriodoRelatorio();
      return;
    }

    const formatarData = (valor) =>
      new Date(valor).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
    const nomesAcoes = {
      CONFIGURACAO_ATUALIZADA: 'Configurações atualizadas',
      PRECO_CONCORRENTE_REGISTRADO: 'Preço de concorrente registrado',
      PRODUTO_CRIADO: 'Produto cadastrado',
      PRODUTO_ATUALIZADO: 'Produto atualizado',
      PRODUTO_DESATIVADO: 'Produto desativado',
      SUGESTAO_GERADA: 'Sugestão de preço gerada',
      SUGESTOES_CATALOGO_GERADAS: 'Sugestões de preço geradas',
      SUGESTAO_DECIDIDA: 'Sugestão de preço decidida',
      USUARIO_CRIADO: 'Membro da equipe cadastrado',
      USUARIO_ATUALIZADO: 'Membro da equipe atualizado',
      USUARIO_DESATIVADO: 'Membro da equipe desativado',
      LOGIN_SUCESSO: 'Login realizado',
      LOGIN_FALHO: 'Tentativa de login sem sucesso',
      LOGIN_BLOQUEADO: 'Acesso bloqueado por tentativas de login',
      SENHA_REDEFINIDA: 'Senha redefinida'
    };
    const nomesCamposHistorico = {
      username: 'Usuário',
      cargo_id: 'Cargo',
      id_produto: 'Código do produto',
      quantidade: 'Quantidade de sugestões',
      preco: 'Preço do concorrente',
      concorrente: 'Concorrente',
      preco_atual: 'Preço anterior',
      preco_sugerido: 'Preço sugerido',
      preco_final: 'Preço final',
      decisao: 'Decisão',
      observacao: 'Observação',
      motivo: 'Motivo',
      margem_minima: 'Margem mínima (%)',
      limiar_giro: 'Limiar de giro',
      dias_validade: 'Dias para validade'
    };
    const valoresHistorico = {
      APROVADA: 'Aprovada',
      EDITADA: 'Editada e aprovada',
      REJEITADA: 'Rejeitada',
      PENDENTE: 'Pendente'
    };
    const formatarDetalhesHistorico = (detalhes) =>
      Object.entries(detalhes || {})
        .filter(([, valor]) => valor !== null && valor !== undefined && valor !== '')
        .map(([chave, valor]) => {
          const nome = nomesCamposHistorico[chave] || chave.replaceAll('_', ' ');
          const exibicao = valoresHistorico[valor] || (
            typeof valor === 'object' ? JSON.stringify(valor) : String(valor)
          );
          return `${nome}: ${exibicao}`;
        })
        .join(' • ');
    const cards = eventos.map((evento) => {
      let tipo;
      let detalhes;
      if (evento.tipo === 'FEEDBACK') {
        tipo = '<span class="history-badge history-feedback">Feedback registrado</span>';
        detalhes = `${evento.cliente ? `<strong>Cliente:</strong> ${escaparHtml(evento.cliente)} — ` : ''}${escaparHtml(evento.mensagem)}`;
      } else if (evento.tipo === 'ESTOQUE') {
        const entrada = evento.tipo_operacao === 'ENTRADA';
        const venda = evento.tipo_operacao === 'VENDA';
        tipo = `<span class="history-badge ${entrada ? 'history-entrada' : 'history-saida'}">${venda ? 'Venda' : entrada ? 'Entrada' : 'Saída'}${venda ? '' : ' de estoque'}</span>`;
        detalhes = `${escaparHtml(evento.quantidade)} unidade(s) — ${escaparHtml(evento.motivo)}`;
      } else if (evento.tipo === 'ATIVIDADE') {
        tipo = '<span class="history-badge history-atividade">Atividade</span>';
        const mensagem = typeof evento.mensagem === 'string'
          ? evento.mensagem
          : formatarDetalhesHistorico(evento.mensagem);
        detalhes = `${escaparHtml(nomesAcoes[evento.acao] || evento.acao)}${mensagem ? ` — ${escaparHtml(mensagem)}` : ''}`;
      } else {
        tipo = '<span class="history-badge history-preco">Alteração de preço</span>';
        detalhes = `De R$ ${escaparHtml(Number(evento.preco_antigo).toFixed(2))} para R$ ${escaparHtml(Number(evento.preco_novo).toFixed(2))} — ${escaparHtml(evento.motivo)}`;
      }
      return `<article class="activity-card">
        <div class="activity-card-top"><time datetime="${escaparHtml(evento.data)}">${escaparHtml(formatarData(evento.data))}</time>${tipo}</div>
        <h2>${escaparHtml(evento.produto)}</h2>
        <p>${detalhes}</p>
        ${evento.usuario_nome
          ? `<small>Realizado por ${escaparHtml(evento.usuario_nome)}</small>`
          : evento.tipo === 'ESTOQUE' && !evento.responsavel_registrado
            ? '<small>Responsável não registrado neste lançamento antigo</small>'
            : ''}
      </article>`;
    }).join('');

    main.innerHTML = `
      <h1>Histórico e Relatórios</h1>
      ${displayModeControl()}
      ${relatorioHtml}
      ${giroHtml}
      <section class="${collectionClass()} activity-grid">${cards}</section>
    `;
    definirPeriodoRelatorio();
  } catch (error) {
    main.innerHTML = `<h1>Histórico e Relatórios</h1><div class="err">${escaparHtml(error.message)}</div>`;
  }
}

function definirPeriodoRelatorio() {
  const hoje = new Date();
  const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
  const iso = (data) => {
    const deslocada = new Date(data.getTime() - data.getTimezoneOffset() * 60000);
    return deslocada.toISOString().slice(0, 10);
  };
  const inicio = document.getElementById('relatorioInicio');
  if (!inicio) return;
  inicio.value = iso(inicioMes);
  document.getElementById('relatorioFim').value = iso(hoje);
}

async function carregarGiroEstoque() {
  const resultado = document.getElementById('giroResultado');
  resultado.textContent = 'Calculando giro...';
  try {
    const produtosGiro = await api('/giro');
    const formatarQuantidade = (valor) =>
      new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 }).format(valor);
    const cards = produtosGiro.map((produto) => `
      <article class="entity-card">
        <h2>${escaparHtml(produto.produto)}</h2>
        <dl class="entity-details">
          <div><dt>Estoque atual</dt><dd>${formatarQuantidade(produto.estoque_atual)}</dd></div>
          <div><dt>Vendas - 7 dias</dt><dd>${formatarQuantidade(produto.quantidade_vendida_7_dias)}</dd></div>
          <div><dt>Vendas - 30 dias</dt><dd>${formatarQuantidade(produto.quantidade_vendida_30_dias)}</dd></div>
        </dl>
      </article>
    `).join('');
    resultado.innerHTML = produtosGiro.length
      ? `<section class="${collectionClass()} entity-grid">${cards}</section>`
      : '<div class="muted">Não há produtos ativos para calcular o giro.</div>';
  } catch (error) {
    resultado.innerHTML = `<div class="err">${escaparHtml(error.message)}</div>`;
  }
}

async function carregarRelatorio() {
  const tipo = document.getElementById('relatorioTipo').value;
  const inicio = document.getElementById('relatorioInicio').value;
  const fim = document.getElementById('relatorioFim').value;
  const resultado = document.getElementById('relatorioResultado');
  if (!inicio || !fim) {
    resultado.innerHTML = '<div class="err">Informe o período do relatório.</div>';
    return;
  }
  resultado.textContent = 'Carregando relatório...';
  try {
    const relatorio = await api(
      `/relatorios?tipo=${encodeURIComponent(tipo)}&inicio=${encodeURIComponent(inicio)}&fim=${encodeURIComponent(fim)}`
    );
    const dados = relatorio.dados;
    let colunas;
    let linhas;
    if (tipo === 'vendas') {
      colunas = ['Produto', 'Quantidade vendida', 'Faturamento'];
      linhas = dados.map(item => [item.produto, item.quantidade, `R$ ${item.faturamento.toFixed(2)}`]);
    } else if (tipo === 'giro') {
      colunas = ['Produto', 'Quantidade vendida', 'Estoque atual'];
      linhas = dados.map(item => [item.produto, item.quantidade_vendida, item.estoque_atual]);
    } else {
      colunas = ['Produto', 'Data', 'Preço anterior', 'Preço novo', 'Motivo'];
      linhas = dados.map(item => [
        item.produto,
        new Date(item.data_alteracao).toLocaleString('pt-BR'),
        `R$ ${Number(item.preco_antigo).toFixed(2)}`,
        `R$ ${Number(item.preco_novo).toFixed(2)}`,
        item.motivo
      ]);
    }
    const cards = linhas.map(linha => `
      <article class="entity-card">
        <h2>${escaparHtml(linha[0])}</h2>
        <dl class="entity-details">
          ${colunas.slice(1).map((coluna, index) => `<div><dt>${escaparHtml(coluna)}</dt><dd>${escaparHtml(linha[index + 1])}</dd></div>`).join('')}
        </dl>
      </article>
    `).join('');
    resultado.innerHTML = dados.length
      ? `<section class="${collectionClass()} entity-grid">${cards}</section>`
      : '<div class="muted">Não há dados para o período selecionado.</div>';
  } catch (error) {
    resultado.innerHTML = `<div class="err">${escaparHtml(error.message)}</div>`;
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
    const cards = comparacao.produtos.map((produto) => `
      <article class="entity-card">
        <h2>${escaparHtml(produto.nome_produto)}</h2>
        <dl class="entity-details">
          ${comparacao.arquivos.map((arquivo) => {
            const precos = produto.precos[arquivo] || [];
            const nome = arquivo.replace(/\.(xlsx|xlsm)$/i, '');
            return `<div><dt>${escaparHtml(nome)}</dt><dd>${precos.length ? precos.map(formatarValor).join(', ') : 'Sem preço registrado'}</dd></div>`;
          }).join('')}
          <div><dt>Diferença de preços</dt><dd>${produto.diferenca === null ? '—' : formatarValor(produto.diferenca)}</dd></div>
        </dl>
      </article>
    `).join('');

    main.innerHTML = `
      <h1>Monitoramento da Concorrência</h1>
      ${displayModeControl()}
      <section class="${collectionClass()} entity-grid">${cards || '<p class="muted">As planilhas não contêm produtos.</p>'}</section>
    `;
  } catch (error) {
    main.innerHTML = `<h1>Monitoramento da Concorrência</h1><div class="err">${escaparHtml(error.message)}</div>`;
  }
}

restaurarSidebar();
restaurarSessao();

let tokenRedefinicaoSenha = null;
function solicitarRecuperacao() {
  document.getElementById('recoveryView').hidden = false;
  document.getElementById('recoveryErr').textContent = '';
}

async function enviarRecuperacao() {
  const email = document.getElementById('recoveryEmail').value.trim();
  if (!email) {
    document.getElementById('recoveryErr').textContent = 'Informe o e-mail cadastrado.';
    return;
  }
  try {
    const resposta = await api('/auth/recuperar-senha', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
    document.getElementById('recoveryErr').textContent = resposta.mensagem;
  } catch (error) {
    document.getElementById('recoveryErr').textContent = error.message;
  }
}

async function confirmarRedefinicao() {
  const novaSenha = document.getElementById('resetPassword').value;
  try {
    const resposta = await api('/auth/redefinir-senha', {
      method: 'POST',
      body: JSON.stringify({
        token: tokenRedefinicaoSenha,
        nova_senha: novaSenha
      })
    });
    document.getElementById('recoveryErr').textContent = resposta.mensagem;
    tokenRedefinicaoSenha = null;
    history.replaceState(null, '', location.pathname);
    document.getElementById('resetPassword').value = '';
  } catch (error) {
    document.getElementById('recoveryErr').textContent = error.message;
  }
}

const resetTokenUrl = new URLSearchParams(location.search).get('reset_token');
if (resetTokenUrl) {
  tokenRedefinicaoSenha = resetTokenUrl;
  document.getElementById('recoveryView').hidden = false;
  document.getElementById('recoveryEmailLabel').hidden = true;
  document.getElementById('recoveryEmail').hidden = true;
  document.querySelector('.login-link').hidden = true;
  document.getElementById('resetPasswordLabel').hidden = false;
  document.getElementById('resetPassword').hidden = false;
  document.getElementById('resetPasswordButton').hidden = false;
}
