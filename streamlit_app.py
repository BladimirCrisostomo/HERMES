"""Interfaz web de HERMES.   Uso:  streamlit run streamlit_app.py"""
import streamlit as st

from src import config
from src.motor import procesar_consulta

config.configurar_logging()
st.set_page_config(page_title="HERMES", page_icon="📡")
st.title("📡 HERMES")
st.caption("Sistema inteligente de administración y diagnóstico de redes")

consulta = st.text_input("¿Qué problema tienes con tu red?",
                         placeholder="Ej: Mi internet está muy lento")

if st.button("Diagnosticar", type="primary") and consulta.strip():
    with st.spinner("Analizando tu red..."):
        r = procesar_consulta(consulta)
    st.write(f"**Intención detectada:** `{r.intencion}`")

    if r.medicion is not None:
        m, d = r.medicion, r.diagnostico
        c1, c2, c3 = st.columns(3)
        c1.metric("Latencia", f"{m.internet.latencia} ms" if m.internet.conexion else "—")
        c2.metric("Pérdida", f"{m.internet.perdida}%")
        c3.metric("Jitter", f"{m.internet.jitter} ms" if m.internet.conexion else "—")
        if m.tiene_gateway and m.gateway.conexion:
            st.caption(f"Router ({m.gateway_ip}): {m.gateway.latencia} ms, "
                       f"pérdida {m.gateway.perdida}%")
        st.subheader("Diagnóstico")
        st.info(d.mensaje)
        st.write("**Recomendación:**", d.recomendacion)
        fuente = "modelo de ML" if d.origen == "ml" else "reglas"
        extra = f" · confianza {d.confianza:.0%}" if d.confianza is not None else ""
        st.caption(f"Fuente: {fuente}{extra}")
    elif r.intencion == "listar_dispositivos" and r.datos.get("dispositivos"):
        st.success(r.mensaje)
        st.dataframe(r.datos["dispositivos"], use_container_width=True)
    elif r.datos.get("correcto") and "canal_recomendado" in r.datos:
        st.success(r.mensaje)
        st.bar_chart(r.datos["redes_por_canal"])
    elif r.datos:
        st.write(r.mensaje)
        st.json(r.datos)
    else:
        st.warning(r.mensaje)
