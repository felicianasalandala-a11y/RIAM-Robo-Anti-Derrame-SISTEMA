import serial
import threading
import time
import random
from database import (
    encontrar_area_proxima, 
    registrar_posicao, 
    registrar_derrame,
    listar_areas,
    listar_robos
)

# ============================================
# VARIÁVEIS GLOBAIS
# ============================================

socketio = None  # Será configurado pelo app.py

# ============================================
# FUNÇÃO PARA PROCESSAR DADOS DO ROBÔ
# ============================================

def processar_dados(dados_str):
    """
    Processa os dados recebidos do robô via LoRa
    Formato esperado: id_robo,fluorescencia,distancia,latitude,longitude
    Exemplo: "1,78,45.2,-23.550400,-46.633900"
    """
    global socketio
    
    try:
        # Separar os dados por vírgula
        partes = dados_str.split(',')
        
        # Verificar se tem 5 partes (id_robo, fluorescencia, distancia, latitude, longitude)
        if len(partes) != 5:
            print(f"⚠️ Formato inválido: {dados_str}")
            print("   O formato esperado é: id_robo,fluorescencia,distancia,latitude,longitude")
            return
        
        # Extrair os valores
        id_robo = int(partes[0])
        fluorescencia = int(partes[1])
        distancia = float(partes[2])
        latitude = float(partes[3])
        longitude = float(partes[4])
        
        # Mostrar no terminal
        print("=" * 60)
        print(f"📡 Dados recebidos do Robô {id_robo}:")
        print(f"   🔬 Fluorescência: {fluorescencia}%")
        print(f"   📏 Distância do obstáculo: {distancia} cm")
        print(f"   📍 Posição: {latitude}, {longitude}")
        
        # Determinar o status da água
        if fluorescencia > 70:
            status = "🔴 DERRAME DETECTADO"
        elif fluorescencia > 40:
            status = "🟡 POSSÍVEL CONTAMINAÇÃO"
        else:
            status = "🟢 NORMAL"
        
        print(f"   📊 Status: {status}")
        
        # Encontrar a área mais próxima
        area = encontrar_area_proxima(latitude, longitude)
        
        if area:
            id_area = area['id']
            nome_area = area['nome']
            print(f"   🗺️ Área mais próxima: {nome_area}")
            
            # Registrar a posição do robô no banco de dados
            registrar_posicao(id_robo, id_area)
            print(f"   ✅ Posição registrada na área: {nome_area}")
            
            # Verificar se é derrame (fluorescência maior que 70%)
            if fluorescencia > 70:
                registrar_derrame(id_area)
                print(f"   🔴🔴🔴 DERRAME REGISTRADO na área {nome_area}!")
                
                # Enviar alerta via WebSocket para o dashboard
                if socketio:
                    socketio.emit('alerta_derrame', {
                        'mensagem': f'🚨 ALERTA! Derrame detectado na área {nome_area}! Intensidade: {fluorescencia}%',
                        'id_robo': id_robo,
                        'area': nome_area,
                        'fluorescencia': fluorescencia,
                        'latitude': latitude,
                        'longitude': longitude
                    })
        else:
            print(f"   ⚠️ Nenhuma área próxima encontrada")
        
        # Enviar leitura normal para o dashboard (WebSocket)
        if socketio:
            socketio.emit('nova_leitura', {
                'id_robo': id_robo,
                'fluorescencia': fluorescencia,
                'distancia': distancia,
                'latitude': latitude,
                'longitude': longitude,
                'area': area['nome'] if area else "Área desconhecida",
                'status': status
            })
        
        print("=" * 60)
        
    except ValueError as e:
        print(f"❌ Erro ao converter dados: {e}")
        print(f"   Dados recebidos: {dados_str}")
    except Exception as e:
        print(f"❌ Erro ao processar dados: {e}")

# ============================================
# FUNÇÃO PARA LER A PORTA SERIAL (LoRa REAL)
# ============================================

def ler_lora_real():
    """Fica escutando a porta serial do gateway LoRa (hardware real)"""
    
    # Lista de portas seriais comuns no Windows
    portas_teste = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8']
    
    ser = None
    porta_encontrada = None
    
    # Tentar encontrar o gateway LoRa
    for porta in portas_teste:
        try:
            print(f"🔍 Tentando conectar na porta {porta}...")
            ser = serial.Serial(porta, 115200, timeout=1)
            porta_encontrada = porta
            print(f"✅ Gateway LoRa conectado na porta {porta_encontrada}")
            break
        except:
            continue
    
    if ser is None:
        print("⚠️ Nenhum gateway LoRa encontrado nas portas:", portas_teste)
        print("🔄 Mudando para modo de simulação...")
        return False
    
    # Loop para ler os dados
    while True:
        try:
            if ser.in_waiting:
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
                if linha:
                    processar_dados(linha)
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ Erro na leitura da porta serial: {e}")
            time.sleep(1)
    
    return True

# ============================================
# FUNÇÃO PARA SIMULAR DADOS (TESTE SEM HARDWARE)
# ============================================

def simular_dados():
    """Gera dados simulados para teste quando não há hardware LoRa"""
    
    print("🔄 Modo de SIMULAÇÃO ativado")
    print("   Gerando dados de teste a cada 5 segundos...")
    print("   Para usar hardware real, conecte o gateway LoRa e reinicie o programa")
    print("-" * 60)
    
    # IDs dos robôs cadastrados (ajuste conforme sua tabela)
    ids_robo = [1, 2]
    
    # Coordenadas de exemplo (Brasil)
    while True:
        # Escolher um robô aleatório
        id_robo = random.choice(ids_robo)
        
        # Gerar valores aleatórios
        fluorescencia = random.randint(0, 100)
        distancia = random.uniform(10, 200)
        
        # Gerar coordenadas próximas às áreas cadastradas
        latitude = -23.5504 + random.uniform(-0.02, 0.02)
        longitude = -46.6339 + random.uniform(-0.02, 0.02)
        
        # Montar a string no formato esperado
        dados_simulados = f"{id_robo},{fluorescencia},{distancia:.1f},{latitude:.6f},{longitude:.6f}"
        
        # Processar os dados simulados
        processar_dados(dados_simulados)
        
        # Aguardar 5 segundos antes da próxima leitura
        time.sleep(5)

# ============================================
# FUNÇÃO PARA INICIAR O RECEPTOR LORA
# ============================================

def iniciar_receptor_lora(socketio_app):
    """Inicia a thread que recebe os dados LoRa"""
    global socketio
    socketio = socketio_app
    
    print("=" * 60)
    print("📡 INICIANDO RECEPTOR LoRa")
    print("=" * 60)
    
    # Primeiro, tenta conectar com hardware real
    # Se não conseguir, entra em modo de simulação
    try:
        # Tenta listar as portas disponíveis
        import serial.tools.list_ports
        portas_disponiveis = [port.device for port in serial.tools.list_ports.comports()]
        
        if portas_disponiveis:
            print(f"🔍 Portas seriais encontradas: {portas_disponiveis}")
        
        # Tentar conectar com hardware real
        def tentar_hardware():
            try:
                # Verificar se alguma porta tem gateway LoRa
                for porta in portas_disponiveis:
                    test_ser = serial.Serial(porta, 115200, timeout=0.5)
                    test_ser.close()
                
                # Se chegou aqui, tenta ler dados reais
                ler_lora_real()
            except:
                print("⚠️ Hardware LoRa não encontrado")
                simular_dados()
        
        # Iniciar thread para o hardware
        thread = threading.Thread(target=tentar_hardware, daemon=True)
        thread.start()
        
    except:
        # Se não conseguir listar portas, vai direto para simulação
        print("⚠️ Não foi possível listar portas seriais")
        print("🔄 Iniciando modo de simulação...")
        
        thread = threading.Thread(target=simular_dados, daemon=True)
        thread.start()
    
    print("✅ Thread de recepção LoRa iniciada")
    print("=" * 60)