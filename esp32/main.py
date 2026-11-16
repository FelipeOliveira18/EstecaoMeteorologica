from machine import Pin, ADC, I2C
import network
import time
import json
import dht
import bmp280

try:
    import urequests
except ImportError:
    urequests = None


# ==========================================
# CONFIGURACAO DAS REDES WI-FI
# ==========================================

REDES_WIFI = [
    ("NOME_DA_REDE_1", "SENHA_DA_REDE_1"),
    ("NOME_DA_REDE_2", "SENHA_DA_REDE_2")
]


# ==========================================
# CONFIGURACAO DO FIREBASE
# ==========================================

FIREBASE_URL = "https://trabalho-26cb3-default-rtdb.firebaseio.com"
FIREBASE_PATH = "/leitura_atual.json"

INTERVALO_LEITURA = 5000


# ==========================================
# PINOS DOS SENSORES
# ==========================================

DHT_PIN = 15

LDR_PIN = 32

MQ135_ANALOG_PIN = 34
MQ135_DIGITAL_PIN = 23

I2C_SDA = 21
I2C_SCL = 22


# ==========================================
# INICIALIZACAO DOS SENSORES
# ==========================================

print("Inicializando sensores...")

# DHT22
sensor_dht = dht.DHT22(Pin(DHT_PIN))

# LDR
ldr = ADC(Pin(LDR_PIN))
ldr.atten(ADC.ATTN_11DB)

# MQ135
mq135_analog = ADC(Pin(MQ135_ANALOG_PIN))
mq135_analog.atten(ADC.ATTN_11DB)

mq135_digital = Pin(MQ135_DIGITAL_PIN, Pin.IN)


# ==========================================
# INICIALIZACAO DO BMP280
# ==========================================

i2c = I2C(
    0,
    sda=Pin(I2C_SDA),
    scl=Pin(I2C_SCL),
    freq=100000
)

bmp = None

try:
    dispositivos = i2c.scan()

    print("Dispositivos I2C encontrados:", dispositivos)

    if 0x76 in dispositivos:
        endereco_bmp = 0x76
    elif 0x77 in dispositivos:
        endereco_bmp = 0x77
    else:
        endereco_bmp = None

    if endereco_bmp is not None:
        bmp = bmp280.BMP280(
            i2c,
            addr=endereco_bmp
        )

        print("BMP280 inicializado!")
        print("Endereco:", hex(endereco_bmp))

    else:
        print("ATENCAO: BMP280 nao encontrado!")

except Exception as erro:
    print("Erro ao inicializar BMP280:", erro)


# ==========================================
# ESTRUTURA DOS DADOS
# ==========================================

dados = {
    "temperatura": None,
    "umidade": None,
    "pressao": None,
    "altitude": None,
    "luminosidade": None,
    "mq135_analogico": None,
    "mq135_digital": None
}


# ==========================================
# CONEXAO WI-FI
# ==========================================

wifi = network.WLAN(network.STA_IF)


def conectar_wifi():

    wifi.active(True)

    if wifi.isconnected():
        print("Wi-Fi ja conectado!")
        print("IP:", wifi.ifconfig()[0])
        return wifi

    for nome, senha in REDES_WIFI:

        if not nome or nome.startswith("NOME_DA_REDE"):
            continue

        print("Tentando conectar:", nome)

        try:
            try:
                wifi.disconnect()
            except Exception:
                pass

            time.sleep(1)

            wifi.connect(nome, senha)

            inicio = time.time()

            while not wifi.isconnected():

                if time.time() - inicio >= 15:
                    print("Falha na rede:", nome)
                    break

                time.sleep(1)

            if wifi.isconnected():
                print("Wi-Fi conectado!")
                print("Rede:", nome)
                print("IP:", wifi.ifconfig()[0])
                return wifi

        except Exception as erro:
            print("Erro Wi-Fi:", erro)

    print("Nenhuma rede Wi-Fi conectada.")

    return wifi


# ==========================================
# LEITURA DOS SENSORES
# ==========================================

def ler_sensores():

    global dados

    # DHT22
    try:
        time.sleep_ms(200)

        sensor_dht.measure()

        dados["temperatura"] = sensor_dht.temperature()
        dados["umidade"] = sensor_dht.humidity()

    except Exception as erro:
        print("Erro no DHT22:", erro)

    # BMP280
    try:
        if bmp is not None:

            pressao_pa = bmp.pressure

            dados["pressao"] = round(
                pressao_pa / 100,
                2
            )

            altitude = 44330 * (
                1 - (pressao_pa / 101325) ** 0.1903
            )

            dados["altitude"] = round(
                altitude,
                2
            )

        else:
            print("BMP280 indisponivel.")

    except Exception as erro:
        print("Erro no BMP280:", erro)

    # LDR
    try:
        dados["luminosidade"] = ldr.read()

    except Exception as erro:
        print("Erro no LDR:", erro)

    # MQ135
    try:
        dados["mq135_analogico"] = mq135_analog.read()

        dados["mq135_digital"] = mq135_digital.value()

    except Exception as erro:
        print("Erro no MQ135:", erro)

    # Mostrar leituras
    print("\n========== LEITURAS ==========")

    print(json.dumps(dados))

    print("==============================\n")


# ==========================================
# ENVIO PARA O FIREBASE
# ==========================================

def enviar_firebase():

    if urequests is None:
        print("Biblioteca urequests nao encontrada!")
        return

    url = FIREBASE_URL + FIREBASE_PATH

    resposta = None

    try:
        resposta = urequests.patch(
            url,
            data=json.dumps(dados),
            headers={
                "Content-Type": "application/json"
            }
        )

        print(
            "Firebase - HTTP:",
            resposta.status_code
        )

        if resposta.status_code not in (200, 204):
            print("Resposta:", resposta.text)

    except Exception as erro:
        print("Erro Firebase:", erro)

    finally:
        if resposta is not None:
            resposta.close()


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

print("\n================================")
print("ESTACAO METEOROLOGICA ESP32")
print("INICIANDO SISTEMA...")
print("================================\n")


# Conectar Wi-Fi
wifi = conectar_wifi()


# Controle do intervalo de leitura
ultima_leitura = (
    time.ticks_ms() - INTERVALO_LEITURA
)


# ==========================================
# LOOP PRINCIPAL
# ==========================================

while True:

    agora = time.ticks_ms()

    if time.ticks_diff(
        agora,
        ultima_leitura
    ) >= INTERVALO_LEITURA:

        ultima_leitura = agora

        # Verificar Wi-Fi
        if not wifi.isconnected():

            print("Wi-Fi desconectado!")

            wifi = conectar_wifi()

        # Ler sensores
        ler_sensores()

        # Enviar para Firebase
        if wifi.isconnected():

            enviar_firebase()

        else:
            print("Sem Wi-Fi. Dados nao enviados.")

    time.sleep_ms(50)