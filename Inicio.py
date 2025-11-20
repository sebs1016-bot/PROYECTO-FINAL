import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
import paho.mqtt.client as paho
import json
from gtts import gTTS
from googletrans import Translator

def on_publish(client,userdata,result):             #create function for callback
    print("el dato ha sido publicado \n")
    pass
def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received=str(message.payload.decode("utf-8"))
    st.write(message_received)

broker="broker.mqttdashboard.com"
port=1883
client1= paho.Client("streamlit_planta_Mazo")
client1.on_message = on_message
# -------------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------------

BROKER = "broker.mqttdashboard.com"
PORT = 1883

TOPIC_VOICE = "voice_ctrlfinal_mazo"    # comandos para el motor
TOPIC_SENSOR = "Sensor/THP2_Mazo"        # datos del sensor

st.set_page_config(page_title="Control de Plantas", layout="centered")

# Animación de fondo
st.markdown("""
<style>
.stApp {
    background: linear-gradient(270deg, #48dbfb, #1dd1a1, #feca57, #ff6b6b);
    background-size: 600% 600%;
    animation: mover 10s ease infinite;
    color: white;
    font-family: 'Montserrat', sans-serif;
}
@keyframes mover {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}
</style>
""", unsafe_allow_html=True)

st.title("🌱 Sistema Inteligente para Plantas")
st.subheader("Control por Voz + Sensor en Tiempo Real")

# -------------------------------------------------------------------
# MQTT (sensor)
# -------------------------------------------------------------------

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Función para obtener un mensaje MQTT"""
    message_received = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except:
            # Si no es JSON, guardar como texto
            message_received["payload"] = message.payload.decode()
            message_received["received"] = True
    
    try:
        client = mqtt.Client(client_id=client_id)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        # Esperar máximo 5 segundos
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    
    except Exception as e:
        return {"error": str(e)}

# Sidebar - Configuración
with st.sidebar:
    st.subheader('⚙️ Configuración de Conexión')
    
    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com', 
                           help='Dirección del broker MQTT')
    
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535,
                           help='Puerto del broker (generalmente 1883)')
    
    topic = st.text_input('Tópico', value='sensor_st',
                          help='Tópico MQTT a suscribirse')
    
    client_id = st.text_input('ID del Cliente', value='streamlit_client',
                              help='Identificador único para este cliente')

# Título
st.title('📡 Lector de Sensor MQTT')

# Información al inicio
with st.expander('ℹ️ Información', expanded=False):
    st.markdown("""
    ### Cómo usar esta aplicación:
    
    1. **Broker MQTT**: Ingresa la dirección del servidor MQTT en el sidebar
    2. **Puerto**: Generalmente es 1883 para conexiones no seguras
    3. **Tópico**: El canal al que deseas suscribirte
    4. **ID del Cliente**: Un identificador único para esta conexión
    5. Haz clic en **Obtener Datos** para recibir el mensaje más reciente
    
    ### Brokers públicos para pruebas:
    - broker.mqttdashboard.com
    - test.mosquitto.org
    - broker.hivemq.com
    """)

st.divider()

# Botón para obtener datos
if st.button('🔄 Obtener Datos del Sensor', use_container_width=True):
    with st.spinner('Conectando al broker y esperando datos...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# Mostrar resultados
if st.session_state.sensor_data:
    st.divider()
    st.subheader('📊 Datos Recibidos')
    
    data = st.session_state.sensor_data
    
    # Verificar si hay error
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Error de conexión: {data['error']}")
    else:
        st.success('✅ Datos recibidos correctamente')
        
        # Mostrar datos en formato JSON
        if isinstance(data, dict):
            # Mostrar cada campo en una métrica
            cols = st.columns(len(data))
            for i, (key, value) in enumerate(data.items()):
                with cols[i]:
                    st.metric(label=key, value=value)
            
            # Mostrar JSON completo
            with st.expander('Ver JSON completo'):
                st.json(data)
        else:
            # Si no es diccionario, mostrar como texto
            st.code(data)
# -------------------------------------------------------------------
# RECONOCIMIENTO DE VOZ 
# -------------------------------------------------------------------

st.header("🎤 Control por voz")

st.subheader("CONTROL POR VOZ")





st.write("Toca el Botón y habla ")

stt_button = Button(label=" Inicio ", width=200)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if result:
    if "GET_TEXT" in result:
        st.write(result.get("GET_TEXT"))
        client1.on_publish = on_publish                            
        client1.connect(broker,port)  
        message =json.dumps({"Act1":result.get("GET_TEXT").strip()})
        ret= client1.publish("voice_ctrlfinal_mazo", message)

    
    try:
        os.mkdir("temp")
    except:
        pass
