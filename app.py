from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO
from database import *
import lora_receiver

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================

app = Flask(__name__)
app.secret_key = 'R.I.A.M_CHAVE_SECRETA_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Iniciar o receptor LoRa com o socketio
lora_receiver.iniciar_receptor_lora(socketio)

# Configurar Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar o sistema'

# ============================================
# CLASSE DO USUÁRIO PARA O FLASK-LOGIN
# ============================================

class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    """Carrega o usuário pelo ID"""
    conn = get_db()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (user_id,))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        return User(usuario['id'], usuario['nome'], usuario['email'])
    return None

# ============================================
# TELA 1: LOGIN
# ============================================

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Tela de login do sistema"""
    
    # Se já estiver logado, vai direto para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Processar o formulário de login
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Buscar usuário no banco
        usuario = buscar_usuario_por_email(email)
        
        # Verificar se usuário existe e senha está correta
        if usuario and usuario['password'] == password:
            # Criar objeto do usuário
            user_obj = User(usuario['id'], usuario['nome'], usuario['email'])
            login_user(user_obj)
            
            # Registrar o login na tabela RegistosLogin
            registrar_login(usuario['id'])
            
            # Redirecionar para o dashboard
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', erro='Email ou senha incorretos')
    
    # Exibir a tela de login
    return render_template('login.html')

# ============================================
# TELA 2: DASHBOARD (MONITORAMENTO)
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Tela principal de monitoramento"""
    
    # Buscar dados para o dashboard
    areas = listar_areas()
    robos = listar_robos()
    total_derrames = contar_derrames()
    
    return render_template('dashboard.html',
                         usuario=current_user.nome,
                         areas=areas,
                         robos=robos,
                         total_derrames=total_derrames)

# ============================================
# TELA 3: REGISTRO DE DERRAMES
# ============================================

@app.route('/registros')
@login_required
def registros():
    """Tela de histórico de derrames"""
    return render_template('registros.html')

# ============================================
# APIs PARA O DASHBOARD (DADOS EM TEMPO REAL)
# ============================================

@app.route('/api/derrames')
def api_derrames():
    """Retorna a lista de derrames para a tabela"""
    derrames = listar_derrames()
    return jsonify(derrames)

@app.route('/api/areas')
def api_areas():
    """Retorna as áreas cadastradas"""
    areas = listar_areas()
    return jsonify(areas)

@app.route('/api/robos')
def api_robos():
    """Retorna os robôs cadastrados"""
    robos = listar_robos()
    return jsonify(robos)

@app.route('/api/estatisticas')
def api_estatisticas():
    """Retorna estatísticas do sistema"""
    return jsonify({
        'total_derrames': contar_derrames(),
        'total_areas': len(listar_areas()),
        'total_robos': len(listar_robos())
    })

@app.route('/api/ultimas_posicoes')
def api_ultimas_posicoes():
    """Retorna as últimas posições dos robôs"""
    limite = request.args.get('limite', 20, type=int)
    posicoes = listar_ultimas_posicoes(limite)
    return jsonify(posicoes)

# ============================================
# LOGOUT
# ============================================

@app.route('/logout')
@login_required
def logout():
    """Faz logout do sistema"""
    logout_user()
    return redirect(url_for('login'))

# ============================================
# INICIALIZAÇÃO DO SISTEMA
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("🌊 R.I.A.M - Robô Inteligente Anti Derrame Marítimo")
    print("=" * 60)
    
    # Testar conexão com o banco
    testar_conexao()
    
    print("\n🚀 Sistema iniciado!")
    print("📍 Acesse no navegador: http://localhost:5000")
    print("📧 Login: use o email cadastrado na tabela usuarios")
    print("=" * 60)
    print("\n💡 Dica: Para testar sem hardware LoRa, o sistema")
    print("   entrará automaticamente em modo de SIMULAÇÃO")
    print("=" * 60)
    print("\n")
    
    # Iniciar o servidor
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)