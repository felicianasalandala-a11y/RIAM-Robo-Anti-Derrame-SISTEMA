import mysql.connector
from mysql.connector import Error

# ============================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================

DB_CONFIG = {
    'host': 'localhost',      # Servidor do MySQL
    'user': 'root',           # Seu usuário do MySQL
    'password': 'root',  # ALTERE PARA SUA SENHA DO MySQL
    'database': 'RIAM'        # Nome do seu banco de dados
}

# ============================================
# FUNÇÃO PARA CONECTAR AO BANCO
# ============================================

def get_db():
    """Retorna uma conexão com o banco de dados RIAM"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Erro ao conectar no MySQL: {e}")
        return None

# ============================================
# FUNÇÃO PARA TESTAR A CONEXÃO
# ============================================

def testar_conexao():
    """Testa se a conexão com o banco está funcionando"""
    conn = get_db()
    if conn:
        print("✅ Conexão com o banco de dados RIAM estabelecida!")
        conn.close()
        return True
    else:
        print("❌ Falha na conexão com o banco de dados!")
        print("   Verifique se o MySQL está rodando e as credenciais estão corretas.")
        return False

# ============================================
# FUNÇÕES PARA USUÁRIOS
# ============================================

def buscar_usuario_por_email(email):
    """Busca um usuário pelo email"""
    conn = get_db()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, email, password FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return usuario

def registrar_login(id_usuario):
    """Registra o login do usuário na tabela RegistosLogin"""
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO RegistosLogin (id_usuarios, data_hora) VALUES (%s, NOW())", (id_usuario,))
    conn.commit()
    
    cursor.close()
    conn.close()
    return True

# ============================================
# FUNÇÕES PARA ÁREAS E ROBÔS
# ============================================

def listar_areas():
    """Retorna todas as áreas cadastradas"""
    conn = get_db()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, latitude, longitude FROM area")
    areas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return areas

def listar_robos():
    """Retorna todos os robôs cadastrados"""
    conn = get_db()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome FROM robo")
    robos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return robos

def encontrar_area_proxima(latitude, longitude):
    """Encontra qual área está mais perto das coordenadas"""
    areas = listar_areas()
    
    if not areas:
        return None
    
    area_mais_proxima = None
    menor_distancia = float('inf')
    
    for area in areas:
        if area['latitude'] and area['longitude']:
            # Cálculo simples de distância
            lat_area = float(area['latitude'])
            lng_area = float(area['longitude'])
            
            distancia = ((latitude - lat_area) ** 2 + (longitude - lng_area) ** 2) ** 0.5
            
            if distancia < menor_distancia:
                menor_distancia = distancia
                area_mais_proxima = area
    
    return area_mais_proxima

# ============================================
# FUNÇÕES PARA REGISTROS DO ROBÔ
# ============================================

def registrar_posicao(id_robo, id_area):
    """Registra a posição do robô na tabela RegistosPosicao"""
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO RegistosPosicao (id_area, data_hora, id_robo) 
        VALUES (%s, NOW(), %s)
    """, (id_area, id_robo))
    conn.commit()
    
    cursor.close()
    conn.close()
    return True

def registrar_derrame(id_area):
    """Registra um derrame na tabela RegistosDerrames"""
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO RegistosDerrames (data_hora, id_area) 
        VALUES (NOW(), %s)
    """, (id_area,))
    conn.commit()
    
    cursor.close()
    conn.close()
    return True

# ============================================
# FUNÇÕES PARA CONSULTAR DADOS
# ============================================

def contar_derrames():
    """Retorna o total de derrames registrados"""
    conn = get_db()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM RegistosDerrames")
    total = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return total

def listar_derrames():
    """Retorna todos os derrames com o nome da área"""
    conn = get_db()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT rd.id, rd.data_hora, a.nome as area_nome 
        FROM RegistosDerrames rd
        JOIN area a ON rd.id_area = a.id
        ORDER BY rd.data_hora DESC
    """)
    derrames = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return derrames

def listar_ultimas_posicoes(limite=20):
    """Retorna as últimas posições registradas"""
    conn = get_db()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT rp.id, rp.data_hora, a.nome as area_nome, rb.nome as robo_nome
        FROM RegistosPosicao rp
        JOIN area a ON rp.id_area = a.id
        JOIN robo rb ON rp.id_robo = rb.id
        ORDER BY rp.data_hora DESC
        LIMIT %s
    """, (limite,))
    
    posicoes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return posicoes