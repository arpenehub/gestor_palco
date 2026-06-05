import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ==========================================================
# CONFIGURAÇÃO
# ==========================================================

st.set_page_config(
    page_title="Gestor de Tempo de Palco",
    layout="wide"
)

# ==========================================================
# CRONOGRAMAS (SEU EVENTO)
# ==========================================================

CRONOGRAMAS = {

    "Sexta": [
        ("Lado Blue", "20:00", 50),
        ("Djs Alien e Azzi", "20:50", 40),
        ("Isis da Mata", "21:30", 60),
        ("Manifesto", "22:30", 5),
        ("Uva de Moc", "22:35", 10),
        ("Desfile Lukah", "22:45", 15),
        ("Dj Breno", "23:00", 60),
    ],

    "Sabado": [
        ("DJ Rudah", "20:00", 20),
        ("Nands e Allysson", "20:20", 15),
        ("Pocket Show Jade", "20:35", 25),
        ("Sebá", "21:00", 60),
        ("Manifesto", "22:00", 10),
        ("Desfile Lukah", "22:10", 15),
        ("Dj Breno", "22:25", 60),
    ]
}

# ==========================================================
# SESSION STATE
# ==========================================================

if "eventos_atraso" not in st.session_state:
    st.session_state.eventos_atraso = {
        "Sexta": [],
        "Sabado": []
    }

# ==========================================================
# DATAFRAME BASE
# ==========================================================


def criar_df(dia):

    dados = CRONOGRAMAS[dia]

    return pd.DataFrame({
        "Evento": [x[0] for x in dados],
        "Inicio Original": [x[1] for x in dados],
        "Duracao Original": [float(x[2]) for x in dados]
    })

# ==========================================================
# DISTRIBUI ATRASO (IGUAL V5.1)
# ==========================================================


def distribuir_atraso(atraso, quantidade):

    base = atraso // quantidade
    resto = atraso % quantidade

    resultado = []

    for i in range(quantidade):
        perda = base
        if i < resto:
            perda += 1
        resultado.append(float(perda))

    return resultado

# ==========================================================
# RECONSTRUIR CRONOGRAMA
# ==========================================================


def reconstruir(dia):

    df = criar_df(dia)

    df["Nova Duracao"] = df["Duracao Original"].astype(float)
    df["Atraso Acumulado"] = 0.0

    eventos = st.session_state.eventos_atraso[dia]

    for e in eventos:

        nome = e["evento"]
        atraso = int(e["atraso"])

        idx = df[df["Evento"] == nome].index[0]

        df.loc[idx, "Atraso Acumulado"] += atraso

        afetadas = df.loc[idx:]

        perdas = distribuir_atraso(atraso, len(afetadas))

        for i, perda in zip(afetadas.index, perdas):

            df.loc[i, "Nova Duracao"] = max(
                0.0,
                float(df.loc[i, "Nova Duracao"]) - perda
            )

    hora = datetime.strptime(df.iloc[0]["Inicio Original"], "%H:%M")

    ini = []
    fim = []

    for _, r in df.iterrows():

        hora += timedelta(minutes=float(r["Atraso Acumulado"]))

        start = hora
        end = start + timedelta(minutes=float(r["Nova Duracao"]))

        ini.append(start.strftime("%H:%M"))
        fim.append(end.strftime("%H:%M"))

        hora = end

    df["Novo Inicio"] = ini
    df["Novo Fim"] = fim

    return df

# ==========================================================
# UI PRINCIPAL
# ==========================================================


st.title("🎵 Gestor de Palco V6.1 (Mobile)")

dia = st.selectbox("📅 Dia do Evento", list(CRONOGRAMAS.keys()))

cronograma = reconstruir(dia)

# ==========================================================
# PRÓXIMO EVENTO
# ==========================================================

# ==========================================================
# RESUMO
# ==========================================================

st.markdown("## 📊 Resumo")

atraso_total = sum(
    e["atraso"] for e in st.session_state.eventos_atraso[dia]
)

col1, col2, col3 = st.columns(3)

col1.metric("Atraso Total", f"{atraso_total} min")

col2.metric(
    "Tempo Total",
    f"{cronograma['Nova Duracao'].sum():.2f} min"
)

col3.metric(
    "Encerramento",
    cronograma.iloc[-1]["Novo Fim"]
)

st.divider()


# ==========================================================
# FORMULÁRIO DE ATRASO (MOBILE FIRST)
# ==========================================================

st.markdown("## ➕ Registrar Atraso")

with st.form("form_atraso"):

    evento = st.selectbox(
        "Evento",
        cronograma["Evento"]
    )

    atraso = st.number_input(
        "Minutos de atraso",
        min_value=0,
        step=1,
        value=0
    )

    ok = st.form_submit_button("Aplicar")

if ok and atraso > 0:

    st.session_state.eventos_atraso[dia].append({
        "evento": evento,
        "atraso": int(atraso)
    })

    st.rerun()

st.divider()


# ==========================================================
# EVENTOS (CARDS MOBILE)
# ==========================================================

st.markdown("## 🎵 Eventos")

for _, r in cronograma.iterrows():

    perda = float(r["Duracao Original"]) - float(r["Nova Duracao"])

    if perda == 0:
        status = "🟢"
    elif perda < r["Duracao Original"]:
        status = "🟡"
    else:
        status = "🔴"

    with st.expander(f"{status} {r['Evento']}"):

        st.write(f"🕒 Início: {r['Novo Inicio']}")
        st.write(f"🕒 Fim: {r['Novo Fim']}")
        st.write(f"⏱ Original: {r['Duracao Original']} min")
        st.write(f"⏱ Atual: {r['Nova Duracao']:.2f} min")
        st.write(f"📉 Perda: {perda:.2f} min")
        st.write(f"⏳ Atraso acumulado: {r['Atraso Acumulado']:.0f} min")

st.divider()

# ==========================================================
# HISTÓRICO
# ==========================================================

st.markdown("## 📜 Histórico")

hist = st.session_state.eventos_atraso[dia]

if not hist:
    st.info("Sem atrasos registrados.")
else:
    for i, h in enumerate(hist, 1):
        st.write(f"{i}. {h['evento']} +{h['atraso']} min")

st.divider()

# ==========================================================
# CONTROLES
# ==========================================================

col1, col2 = st.columns(2)

with col1:
    if st.button("↩ Desfazer último"):
        if st.session_state.eventos_atraso[dia]:
            st.session_state.eventos_atraso[dia].pop()
            st.rerun()

with col2:
    if st.button(f"🗑 Reset {dia}"):
        st.session_state.eventos_atraso[dia] = []
        st.rerun()
