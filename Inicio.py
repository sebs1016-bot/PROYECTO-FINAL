import os
import time
import json
import streamlit as st
from PIL import Image

# ---- MQTT ----
import paho.mqtt.client as mqtt

# ---- VOZ ----
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# ---------------------------- CONFIGURACIÓN PÁGINA -----------------------------
st.set_page_config(page_title="Control de Planta", layout="centered")

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
st.subheader("Control por Voz + Sensor de Humedad y Temperatura")


# ---------------------------- MQTT CONFIG --------------------------------------
BROKER = "broker.mqttdashboard.com"
PORT = 1883

TOPIC_VOICE = "voice_ctrlprueba"          # donde se envía el comando del motor
TOPIC_SENSOR = "Sensor/THP2"             # donde tu Arduino manda los datos de humedad

client = mqtt.Client("streamlit_planta_mazo")

sensor_data = {"humedad": None, "temperatura": None}


# ---------------------------- HANDLERS MQTT ------------------------------------
def on_message(client, userdata, message):
    global sensor_data
    try:
        payload = json.loads(message.payload.decode())
        sensor_data = payload
    except:
        pass

client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(TOPIC_SENSOR)
client.loop_start()

# ---------------------------- SECCIÓN SENSOR -----------------------------------
st.header("📡 Datos del Sensor")

if st.button("Actualizar Sensor"):
    time.sleep(2)
    st.write(sensor_data)

    if sensor_data["humedad"] is not None:
        humedad = float(sensor_data["humedad"])
        
        if humedad < 40:
            st.error(f"🚨 Humedad baja ({humedad}%)")
            st.warning("El sistema recomienda abrir el motor.")
            st.info("Di por voz: **abrir motor**")

        else:
            st.success(f"Humedad adecuada: {humedad}%")
    else:
        st.warning("Aún no llegan datos del sensor.")


# ---------------------------- CONTROL POR VOZ ----------------------------------
st.header("🎤 Control por Voz")

st.write("Toca el botón y habla:")

stt_button = Button(label="🎙 Iniciar reconocimiento", width=250)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "es-ES";

    recognition.onresult = function (e) {
        var value = e.results[0][0].transcript;
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
    };
    recognition.start();
    """))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    debounce_time=0,
    refresh_on_update=False,
    override_height=75
)

if result and "GET_TEXT" in result:
    comando = result.get("GET_TEXT").strip().lower()
    st.write("Comando detectado:", comando)

    # Publica comando
    mensaje = json.dumps({"Act1": comando})
    client.publish(TOPIC_VOICE, mensaje)

    # Acciones automáticas
    if "abrir" in comando:
        st.success("🔓 Motor ABIERTO")

    elif "cerrar" in comando:
        st.warning("🔒 Motor CERRADO")
