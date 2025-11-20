import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

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

client = mqtt.Client("streamlit_planta")
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
# RECONOCIMIENTO DE VOZ (SIN BOKEH)
# -------------------------------------------------------------------

st.header("🎤 Control por voz")

# Inicializa variable
if "voz" not in st.session_state:
    st.session_state["voz"] = ""

# Botón HTML + JS
st.markdown("""
<button id="btnHablar" style="
    padding: 10px 20px;
    background-color:#1dd1a1;
    color:black;
    border:none;
    border-radius:10px;
    font-size:20px;
    cursor:pointer;">
    🎙 Iniciar voz
</button>

<script>
const btn = document.getElementById("btnHablar");

btn.onclick = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "es-ES";
    recognition.continuous = false;

    recognition.onresult = (event) => {
        const texto = event.results[0][0].transcript;
        window.parent.postMessage({type: "vozStreamlit", data: texto}, "*");
    };

    recognition.start();
};
</script>
""", unsafe_allow_html=True)

# Recibir mensaje del navegador
voice_input = st.experimental_get_query_params()
st.markdown("""
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === "vozStreamlit") {
        const texto = event.data.data;
        const params = new URLSearchParams(window.location.search);
        params.set("voz", texto);
        window.location.search = params.toString();
    }
});
</script>
""", unsafe_allow_html=True)

# Procesar voz recibida
voz = voice_input.get("voz", [""])[0]

if voz:
    st.session_state["voz"] = voz
    st.success("Comando detectado: " + voz)

    # Enviar a MQTT
    mensaje = json.dumps({"Act1": voz})
    client.publish(TOPIC_VOICE, mensaje)

    # Feedback
    if "abrir" in voz.lower():
        st.success("🔓 Motor ABIERTO")
    elif "cerrar" in voz.lower():
        st.warning("🔒 Motor CERRADO")
