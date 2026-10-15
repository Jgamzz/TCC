function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s ease-out forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

const CONFIGURACOES_STORAGE_KEY = 'sgb_varejo_configuracoes';
const CONFIGURACOES_PADRAO = {
  margem_minima: 15,
  dias_validade: 7,
  limiar_giro: 10
};

function carregarConfiguracoesLocais() {
  let configuracoes = CONFIGURACOES_PADRAO;
  try {
    configuracoes = Object.assign(
      {},
      CONFIGURACOES_PADRAO,
      JSON.parse(localStorage.getItem(CONFIGURACOES_STORAGE_KEY)) || {}
    );
  } catch(e) {}

  document.getElementById('cfg_margem').value = configuracoes.margem_minima;
  document.getElementById('cfg_dias_validade').value = configuracoes.dias_validade;
  document.getElementById('cfg_limiar_giro').value = configuracoes.limiar_giro;
}

// --- PRODUTOS ---
function openProdutoModal(id){
  editingId = id;
  document.getElementById('produtoErr').textContent = '';
  const bg = document.getElementById('produtoModalBg');
  if (id === null) {
		document.getElementById('produtoModalTitle').textContent = 'Registar produto';
		['f_nome', 'f_custo', 'f_preco', 'f_estoque', 'f_validade'].forEach(fid => document.getElementById(fid).value = '');
  } else {
		const p = produtos.find(x => x.id_produto === id || x.id === id);
		document.getElementById('produtoModalTitle').textContent = 'Alterar produto';
		document.getElementById('f_nome').value = p.nome;
		document.getElementById('f_custo').value = p.custo;
		document.getElementById('f_preco').value = p.preco_atual;
		document.getElementById('f_estoque').value = p.estoque;
		document.getElementById('f_validade').value = p.data_validade ? p.data_validade.split('T')[0] : '';
  }
  bg.classList.add('shown');
}
function closeProdutoModal(){ document.getElementById('produtoModalBg').classList.remove('shown'); }

async function saveProduto(){
  const dados = {
		nome: document.getElementById('f_nome').value.trim(),
		custo: parseFloat(document.getElementById('f_custo').value),
		preco_atual: parseFloat(document.getElementById('f_preco').value),
		estoque: parseInt(document.getElementById('f_estoque').value || 0),
		data_validade: document.getElementById('f_validade').value || null,
  };
  if (!dados.nome || isNaN(dados.custo) || isNaN(dados.preco_atual)) return document.getElementById('produtoErr').textContent = 'Preencha nome, custo e preço.';
  try {
		if (editingId === null) await api('/produtos/', { method: 'POST', body: JSON.stringify(dados) });
		else await api('/produtos/' + editingId, { method: 'PUT', body: JSON.stringify(dados) });
		closeProdutoModal();
		await refreshProdutos();
		render();
  } catch(e) { document.getElementById('produtoErr').textContent = e.message; }
}

async function deleteProduto(id){
  if (!confirm('Excluir este produto?')) return;
  try { await api('/produtos/' + id, { method: 'DELETE' }); await refreshProdutos(); render(); }
  catch(e){ showToast(e.message, 'error'); }
}

// --- MOVIMENTAÇÃO DE ESTOQUE (Entrada, Saída e Venda) ---
function openMovimentacaoModal(idProduto, tipoInicial = ''){
  const produto = produtos.find(p => String(p.id_produto) === String(idProduto))
    || produtos[0];
  if (!produto) {
    showToast('Cadastre um produto antes de movimentar o estoque.', 'error');
    return;
  }

  document.getElementById('m_produto').value = produto.id_produto;
  document.getElementById('m_produto_nome').textContent = produto.nome;
  document.getElementById('m_produto_estoque').textContent = `Estoque atual: ${produto.estoque} un.`;
  document.querySelectorAll('input[name="m_tipo"]').forEach((opcao) => {
    opcao.checked = opcao.value === tipoInicial;
  });
  document.getElementById('m_qtd').value = '';
  document.getElementById('m_motivo').value = '';
  document.getElementById('movimentacaoErr').textContent = '';
  document.getElementById('movimentacaoModalBg').classList.add('shown');
}

function closeMovimentacaoModal(){ document.getElementById('movimentacaoModalBg').classList.remove('shown'); }

function abrirMovimentacaoRapida(idProduto, tipoStr) {
  openMovimentacaoModal(idProduto, tipoStr || '');
}

async function registrarMovimentacao() {
  const dadosOp = {
      id_produto: parseInt(document.getElementById('m_produto').value),
      quantidade: Number(document.getElementById('m_qtd').value)
  };
  const tipo = document.querySelector('input[name="m_tipo"]:checked')?.value;
  const motivo = document.getElementById('m_motivo').value.trim();

  if (!dadosOp.id_produto || !Number.isFinite(dadosOp.quantidade) || dadosOp.quantidade <= 0) {
      return document.getElementById('movimentacaoErr').textContent = 'Informe uma quantidade válida.';
  }
  if (!tipo) {
      return document.getElementById('movimentacaoErr').textContent = 'Selecione o tipo de operação.';
  }
  if (tipo !== 'VENDA' && !motivo) {
      return document.getElementById('movimentacaoErr').textContent = 'O motivo é obrigatório.';
  }

  try {
      if (tipo === 'VENDA') {
          await api('/vendas', { method: 'POST', body: JSON.stringify(dadosOp) });
          showToast('Venda registrada com sucesso!');
      } else {
          await api('/estoque/', {
            method: 'POST',
            body: JSON.stringify({
              ...dadosOp,
              tipo_operacao: tipo,
              motivo
            })
          });
          showToast('Movimentação registrada com sucesso!');
      }
      closeMovimentacaoModal();
      await refreshProdutos();
      render();
  } catch(e) { document.getElementById('movimentacaoErr').textContent = 'Erro: ' + e.message; }
}

// --- FUNÇÕES EXTRAS PARA SUGESTÕES (Editar) ---
function abrirModalEditarSugestao(idSugestao, precoSugeridoAtual) {
  document.getElementById('es_id_sugestao').value = idSugestao;
  document.getElementById('es_preco').value = precoSugeridoAtual;
  document.getElementById('es_motivo').value = '';
  document.getElementById('editSugestaoModalBg').classList.add('shown');
}

function closeEditSugestaoModal() {
  document.getElementById('editSugestaoModalBg').classList.remove('shown');
}

async function salvarSugestaoEditada() {
  const idSugestao = document.getElementById('es_id_sugestao').value;
  const preco = parseFloat(document.getElementById('es_preco').value);
  const observacao = document.getElementById('es_motivo').value.trim();

  if (isNaN(preco) || preco <= 0) return showToast('Insira um preço válido.', 'error');
  if (!observacao) return showToast('A observação é obrigatória ao editar um preço.', 'error');

  try {
      await api('/sugestoes/' + idSugestao, {
          method: 'PATCH',
          body: JSON.stringify({ decisao: 'EDITADA', preco: preco, observacao: observacao })
      });
      closeEditSugestaoModal();
      showToast('Sugestão editada e aprovada!');
      await refreshProdutos();
      render();
  } catch(e) { showToast('Erro: ' + e.message, 'error'); }
}

// --- CONCORRÊNCIA (NOVO) ---
function abrirModalConcorrencia(idProduto) {
  document.getElementById('c_produto_id').value = idProduto;
  document.getElementById('c_valor').value = '';
  document.getElementById('concorrenciaModalBg').classList.add('shown');
}
function closeConcorrenciaModal() { document.getElementById('concorrenciaModalBg').classList.remove('shown'); }

async function salvarConcorrencia() {
  const dados = { id_produto: parseInt(document.getElementById('c_produto_id').value), valor: parseFloat(document.getElementById('c_valor').value) };
  if (!dados.id_produto || isNaN(dados.valor) || dados.valor <= 0) return showToast('Insira um valor válido.', 'error');
  try {
		await api('/concorrentes', { method: 'POST', body: JSON.stringify(dados) });
		closeConcorrenciaModal();
		showToast('Preço da concorrência registrado com sucesso!');
  } catch(e) { showToast('Erro: ' + e.message, 'error'); }
}

// --- SUGESTÕES ---
async function pedirSugestaoDesconto(idProduto) {
  try {
		await api('/sugestoes', { method: 'POST', body: JSON.stringify({ id_produto: idProduto }) });
    showToast('Análise concluída! Vá até a aba "Gestão" para aprovar o novo preço.');
  } catch (e) { showToast('Erro: ' + e.message, 'error'); }
}
async function decidirSugestao(idSugestao, decisaoStr) {
  try {
		await api('/sugestoes/' + idSugestao, { method: 'PATCH', body: JSON.stringify({ decisao: decisaoStr }) });
		await refreshProdutos(); render();
  } catch(e) { showToast('Erro: ' + e.message, 'error'); }
}

// --- GESTÃO DE EQUIPA ---
let editingUserId = null;

function openUsuarioModal(id) {
  editingUserId = id;
  document.getElementById('usuarioErr').textContent = '';
  const bg = document.getElementById('usuarioModalBg');
  
  if (id === null) {
    document.getElementById('usuarioModalTitle').textContent = 'Adicionar Membro';
    document.getElementById('u_name').value = '';
    document.getElementById('u_username').value = '';
    document.getElementById('u_password').value = '';
    document.getElementById('u_senha_hint').textContent = '(Obrigatório)';
    document.getElementById('u_cargo').value = '3';
    document.getElementById('u_status').value = 'true';
  } else {
    const u = usuarios.find(x => x.ID === id);
    document.getElementById('usuarioModalTitle').textContent = 'Alterar Membro';
    document.getElementById('u_name').value = u.Name;
    document.getElementById('u_username').value = u.Username;
    document.getElementById('u_password').value = '';
    document.getElementById('u_senha_hint').textContent = '(Deixe em branco para manter a senha atual)';
    document.getElementById('u_cargo').value = u.Cargo_ID || '3';
    document.getElementById('u_status').value = u.Is_Active ? 'true' : 'false';
  }
  bg.classList.add('shown');
}

function closeUsuarioModal() { document.getElementById('usuarioModalBg').classList.remove('shown'); }

async function saveUsuario() {
  const dados = {
    Name: document.getElementById('u_name').value.trim(),
    Username: document.getElementById('u_username').value.trim(),
    Cargo_ID: parseInt(document.getElementById('u_cargo').value),
    Is_Active: document.getElementById('u_status').value === 'true'
  };
  
  const pwd = document.getElementById('u_password').value.trim();
  if (pwd) dados.Password = pwd;

  if (!dados.Name || !dados.Username) return document.getElementById('usuarioErr').textContent = 'Nome e Login são obrigatórios.';
  if (editingUserId === null && !dados.Password) return document.getElementById('usuarioErr').textContent = 'A senha é obrigatória para novos membros.';

  try {
    if (editingUserId === null) {
      await api('/usuarios/', { method: 'POST', body: JSON.stringify(dados) });
    } else {
      await api('/usuarios/' + editingUserId, { method: 'PUT', body: JSON.stringify(dados) });
    }
    
    closeUsuarioModal();
    await refreshUsuarios();
    render();
  } catch(e) {
    document.getElementById('usuarioErr').textContent = e.message;
  }
}

async function deleteUsuario(id) {
  if (!confirm('Excluir este membro da equipa? Esta ação não pode ser desfeita.')) return;
  try {
    await api('/usuarios/' + id, { method: 'DELETE' });
    await refreshUsuarios();
    render();
  }
  catch(e) { showToast(e.message, 'error'); }
}

// --- FEEDBACK DE CLIENTES ---
function abrirModalFeedback(idProduto) {
  document.getElementById('f_fb_produto_id').value = idProduto;
  document.getElementById('f_fb_cliente').value = '';
  document.getElementById('f_fb_comentario').value = '';
  document.getElementById('feedbackErr').textContent = '';
  document.getElementById('feedbackModalBg').classList.add('shown');
}

function closeFeedbackModal() {
  document.getElementById('feedbackModalBg').classList.remove('shown');
}

async function salvarFeedback() {
  const dados = {
    id_produto: parseInt(document.getElementById('f_fb_produto_id').value),
    cliente: document.getElementById('f_fb_cliente').value.trim(),
    comentario: document.getElementById('f_fb_comentario').value.trim()
  };
  
  if (!dados.comentario) {
    return document.getElementById('feedbackErr').textContent = 'O comentário é obrigatório.';
  }

  try {
    await api('/feedbacks', {
      method: 'POST',
      body: JSON.stringify(dados)
    });
    
    closeFeedbackModal();
    showToast('Feedback registrado com sucesso!');
  } catch(e) {
    document.getElementById('feedbackErr').textContent = 'Erro: ' + e.message;
  }
}

function salvarConfiguracoes() {
  const configuracoes = {
    margem_minima: Number(document.getElementById('cfg_margem').value),
    dias_validade: Number(document.getElementById('cfg_dias_validade').value),
    limiar_giro: Number(document.getElementById('cfg_limiar_giro').value)
  };

  if (!Number.isFinite(configuracoes.margem_minima) || configuracoes.margem_minima < 0 || configuracoes.margem_minima > 100) {
    return showToast('A margem deve estar entre 0% e 100%.', 'error');
  }
  if (!Number.isInteger(configuracoes.dias_validade) || configuracoes.dias_validade < 1) {
    return showToast('Informe pelo menos 1 dia de validade.', 'error');
  }
  if (!Number.isInteger(configuracoes.limiar_giro) || configuracoes.limiar_giro < 0) {
    return showToast('O limiar de giro não pode ser negativo.', 'error');
  }

  localStorage.setItem(CONFIGURACOES_STORAGE_KEY, JSON.stringify(configuracoes));
  showToast('Configurações salvas neste navegador.');
}