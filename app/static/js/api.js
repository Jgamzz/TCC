let API_BASE = document.getElementById('apiBaseInput') ? document.getElementById('apiBaseInput').value : 'http://localhost:5000/api';
let user = null;
let accessToken = null;
let produtos = [];
let usuarios = [];
let currentPage = 'inicio';
let editingId = null;

const CARGO_DONO = 1, CARGO_GER = 2, CARGO_FUNC = 3;
const SESSION_KEY = 'sgb_varejo_session';

function tokenExpirado(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
        return payload.exp ? payload.exp * 1000 <= Date.now() : true;
    } catch(e) {
        return true;
    }
}

function mostrarAplicacao() {
    document.getElementById('loginView').style.display = 'none';
    document.getElementById('app').classList.add('shown');
    document.getElementById('userName').textContent = user.nome || user.Name || 'Utilizador';
    document.getElementById('avatarLetter').textContent = (user.cargo_nome || user.Cargo_Name || '?')[0].toUpperCase();
}

async function iniciarSessao() {
    if (!accessToken || !user) return;
    mostrarAplicacao();
    if (typeof buildNav === 'function') buildNav();
    await refreshProdutos();
    if (typeof render === 'function') render();
}

async function restaurarSessao() {
    try {
        const sessao = JSON.parse(localStorage.getItem(SESSION_KEY));
        if (!sessao || !sessao.accessToken || !sessao.user || tokenExpirado(sessao.accessToken)) {
            localStorage.removeItem(SESSION_KEY);
            return;
        }
        accessToken = sessao.accessToken;
        user = sessao.user;
        await iniciarSessao();
    } catch(e) {
        localStorage.removeItem(SESSION_KEY);
    }
}

async function api(path, opts={}) {
    const headers = Object.assign({'Content-Type':'application/json'}, opts.headers||{});
    if (accessToken) headers.Authorization = 'Bearer ' + accessToken;
    const res = await fetch(API_BASE + path, Object.assign({}, opts, {headers}));
    let body = null;
    try { body = await res.json(); } catch(e){}
    if (!res.ok) throw new Error((body && (body.erro||body.message)) || ('Erro HTTP ' + res.status));
        return body;
}

async function refreshUsuarios() {
    try {
        usuarios = await api('/usuarios/');
    } catch(e) {
        usuarios = [];
        alert('Erro ao carregar a equipa: ' + e.message);
    }
}

async function refreshProdutos() {
    try { produtos = await api('/produtos/'); }
    catch(e) { produtos = []; alert('Erro ao carregar produtos: ' + e.message); }
}

async function doLogin(){
    const email = document.getElementById('loginEmail').value.trim();
    const senha = document.getElementById('loginSenha').value.trim();
    if (!email || !senha) return document.getElementById('loginErr').textContent = 'Preencha o e-mail e a senha.';

    try {
    const resp = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ Username: email, Password: senha })
    });
    accessToken = resp.access_token;
    user = resp.usuario;
    localStorage.setItem(SESSION_KEY, JSON.stringify({ accessToken, user }));
    await iniciarSessao();
    } catch(e) {
        document.getElementById('loginErr').textContent = 'Erro ao entrar: ' + e.message;
    }
}

function logout(){
    user = null;
    accessToken = null;
    localStorage.removeItem(SESSION_KEY);
    document.getElementById('app').classList.remove('shown');
    document.getElementById('loginView').style.display = 'flex';
}