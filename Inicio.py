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

sensor_data = {"humedad": None, "temperatura": None}

def on_message(client, userdata, message):
    global sensor_data
    try:
        payload = json.loads(message.payload.decode())
        sensor_data = payload
    except:
        pass

client = mqtt.Client("streamlit_planta_Mazo")
client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(TOPIC_SENSOR)
client.loop_start()

# -------------------------------------------------------------------
# BOTÓN PARA LEER SENSOR
# -------------------------------------------------------------------

st.header("📡 Datos del sensor")

if st.button("Actualizar datos"):
    time.sleep(1)
    st.write(sensor_data)

    if sensor_data["humedad"] is not None:
        h = float(sensor_data["humedad"])

        if h < 40:
            st.error(f"🚨 Humedad baja ({h}%)")
            st.warning("Di: 'abrir motor'")
        else:
            st.success(f"Humedad adecuada: {h}%")

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
        ret= client1.publish("voice_ctrl", message)

    
    try:
        os.mkdir("temp")
    except:
        pass
