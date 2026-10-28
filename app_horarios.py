import streamlit as st
import json
import os

st.set_page_config(page_title="Palantir School - Gestor de Horarios", layout="wide")

ARCHIVO_DATOS = "datos_centro.json"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
FRANJAS_PRIMARIA = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 12:30 (Recreo)", "12:30 - 13:15", "13:15 - 14:00"]
FRANJAS_INFANTIL = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 11:30 (Almuerzo)", "11:30 - 12:00 (Recreo)", "12:00 - 12:30", "12:30 - 13:15", "13:15 - 14:00"]

LISTA_CURSOS = [
    "Infantil 3 Años", "Infantil 4 Años", "Infantil 5 Años",
    "1º Primaria", "2º Primaria", "3º Primaria", "4º Primaria", "5º Primaria", "6º Primaria"
]

LISTA_PROYECTOS = [
    "Coordinador/a de Ciclo",
    "Coord. Plan Lector / Biblioteca",
    "Coord. Competencia Digital (TIC)",
    "Coord. Igualdad y Convivencia",
    "Coord. Salud / Deporte Escolar",
    "Coord. Bilingüismo / Proyectos Europeos",
    "Equipo Directivo / Otra Libranza"
]

OPCIONES_FRANJA_PRIORITARIA = [
    "Sin preferencia (Automático)",
    "1ª Franja Mañana (9:00 - 11:00)",
    "Mañana Completa (9:00 - 12:00)",
    "Última de la Mañana (11:00 - 12:00)",
    "Tarde (12:30 - 14:00)"
]

# ==========================================
# GESTIÓN DE PERSISTENCIA EN DISCO (JSON)
# ==========================================
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "config_guardada": False,
        "aulas": [],
        "especialistas": [],
        "horarios_aula": {},
        "horarios_tutor": {},
        "horarios_esp": {}
    }

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()
if "vista_detalle" not in st.session_state:
    st.session_state.vista_detalle = None
if "tipo_detalle" not in st.session_state:
    st.session_state.tipo_detalle = None

datos = st.session_state.datos

# Estilos CSS
st.markdown("""
    <style>
    .main-header { font-size: 26px; font-weight: 700; color: #1F4E79; margin-bottom: 10px; }
    .sub-header { font-size: 19px; font-weight: 600; color: #2F5597; margin-top: 15px; margin-bottom: 10px; }
    .stButton>button, .stDownloadButton>button { width: 100%; border-radius: 8px; font-weight: 600; height: 46px; }
    .tabla-horario { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 20px; font-family: sans-serif; font-size: 14px; }
    .tabla-horario th { background-color: #1F4E79; color: white; padding: 10px; text-align: center; border: 1px solid #cbd5e1; width: 16%; }
    .tabla-horario td { padding: 10px; text-align: center; border: 1px solid #cbd5e1; background-color: #ffffff; color: #1e293b; }
    .celda-esp { background-color: #e0f2fe !important; font-weight: 600; color: #0369a1 !important; }
    .celda-apoyo { background-color: #fef3c7 !important; font-weight: 600; color: #b45309 !important; }
    .celda-libre { background-color: #dcfce7 !important; font-weight: 600; color: #15803d !important; }
    .recreo-row td { background-color: #f1f5f9 !important; font-weight: bold; color: #64748b !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# MOTOR PALANTIR: AUTOGENERACIÓN DE HORARIOS
# ==========================================
def inicializar_matrices_base():
    datos["horarios_aula"] = {}
    datos["horarios_tutor"] = {}
    datos["horarios_esp"] = {}

    for a in datos["aulas"]:
        nivel_aula = a.get("nivel", "3º Primaria")
        es_inf = "Infantil" in nivel_aula
        franjas = FRANJAS_INFANTIL if es_inf else FRANJAS_PRIMARIA
        datos["horarios_aula"][a["aula"]] = {}
        datos["horarios_tutor"][a["aula"]] = {}
        for f in franjas:
            if "Recreo" in f or "Almuerzo" in f:
                datos["horarios_aula"][a["aula"]][f] = {d: "RECREO" for d in DIAS}
                datos["horarios_tutor"][a["aula"]][f] = {d: "RECREO" for d in DIAS}
            else:
                datos["horarios_aula"][a["aula"]][f] = {d: a["tutor"] for d in DIAS}
                datos["horarios_tutor"][a["aula"]][f] = {d: f"En su aula ({a['aula']})" for d in DIAS}

    for e in datos["especialistas"]:
        id_esp = f"{e['nombre']} ({e['area']})"
        datos["horarios_esp"][id_esp] = {}
        for f in FRANJAS_PRIMARIA:
            if "Recreo" in f:
                datos["horarios_esp"][id_esp][f] = {d: "RECREO" for d in DIAS}
            else:
                datos["horarios_esp"][id_esp][f] = {d: "Disponible / Apoyo" for d in DIAS}

def buscar_especialista_obj(area_buscada, nivel_aula):
    candidatos = [e for e in datos["especialistas"] if e["area"] == area_buscada]
    if not candidatos:
        return None
    for c in candidatos:
        cursos_pref = c.get("cursos", ["Todos los cursos"])
        if "Todos los cursos" in cursos_pref or nivel_aula in cursos_pref:
            return c
    return candidatos[0]

def ordenar_franjas_por_prioridad(franjas_base, prioridad):
    if prioridad == "1ª Franja Mañana (9:00 - 11:00)":
        pref = [f for f in franjas_base if f in ["9:00 - 10:00", "10:00 - 11:00"]]
    elif prioridad == "Última de la Mañana (11:00 - 12:00)":
        pref = [f for f in franjas_base if f == "11:00 - 12:00"]
    elif prioridad == "Mañana Completa (9:00 - 12:00)":
        pref = [f for f in franjas_base if f in ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00"]]
    elif prioridad == "Tarde (12:30 - 14:00)":
        pref = [f for f in franjas_base if f in ["12:30 - 13:15", "13:15 - 14:00"]]
    else:
        pref = []
    resto = [f for f in franjas_base if f not in pref]
    return pref + resto

def autogenerar_cuadrante():
    inicializar_matrices_base()

    carga_por_nivel = {
        "Infantil 3 Años": [("Inglés", 2, 0), ("Educación Física (EF)", 1, 0), ("Música / Artística", 1, 0), ("Religión", 1, 0)],
        "Infantil 4 Años": [("Inglés", 2, 0), ("Educación Física (EF)", 1, 0), ("Música / Artística", 1, 0), ("Religión", 1, 0)],
        "Infantil 5 Años": [("Inglés", 2, 0), ("Educación Física (EF)", 1, 0), ("Música / Artística", 1, 0), ("Religión", 1, 0)],
        "1º Primaria": [("Inglés", 1, 2), ("Educación Física (EF)", 1, 2), ("Música / Artística", 1, 2), ("Religión", 1, 0)],
        "2º Primaria": [("Educación Física (EF)", 1, 2), ("Música / Artística", 1, 2), ("Religión", 1, 0), ("Inglés", 1, 2)],
        "3º Primaria": [("Inglés", 2, 2), ("Educación Física (EF)", 1, 2), ("Música / Artística", 1, 2), ("Religión", 1, 0)],
        "4º Primaria": [("Inglés", 2, 2), ("Educación Física (EF)", 1, 2), ("Música / Artística", 1, 2), ("Religión", 1, 0)],
        "5º Primaria": [("Inglés", 2, 2), ("Educación Física (EF)", 1, 2), ("Música / Artística", 2, 0), ("Religión", 1, 0)],
        "6º Primaria": [("Inglés", 3, 1), ("Educación Física (EF)", 1, 2), ("Música / Artística", 2, 0), ("Religión", 1, 0)],
    }

    franjas_m_inf = ["9:00 - 10:00", "10:00 - 11:00"]
    franjas_m_pri = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00"]
    franjas_t_pri = ["12:30 - 13:15", "13:15 - 14:00"]

    for a in datos["aulas"]:
        nom_aula = a["aula"]
        nivel = a.get("nivel", "3º Primaria")
        tutor = a["tutor"]
        es_inf = "Infantil" in nivel
        requisitos = carga_por_nivel.get(nivel, [])

        for area, ses_m, ses_t in requisitos:
            esp_obj = buscar_especialista_obj(area, nivel)
            if not esp_obj:
                continue
            id_esp = f"{esp_obj['nombre']} ({esp_obj['area']})"
            prio_franja = esp_obj.get("franja_prioritaria", "Sin preferencia (Automático)")

            if nivel == "2º Primaria":
                if area == "Inglés":
                    dias_validos = ["Miércoles", "Jueves", "Viernes"]
                else:
                    dias_validos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
            else:
                dias_validos = DIAS

            franjas_m_base = franjas_m_inf if es_inf else franjas_m_pri
            franjas_m = ordenar_franjas_por_prioridad(franjas_m_base, prio_franja)

            colocadas_m = 0
            for f in franjas_m:
                for d in dias_validos:
                    if colocadas_m < ses_m:
                        aula_libre = (datos["horarios_aula"][nom_aula][f][d] == tutor)
                        esp_libre = (datos["horarios_esp"][id_esp][f][d] == "Disponible / Apoyo")
                        if aula_libre and esp_libre:
                            datos["horarios_aula"][nom_aula][f][d] = id_esp
                            datos["horarios_esp"][id_esp][f][d] = f"Aula: {nom_aula}"
                            datos["horarios_tutor"][nom_aula][f][d] = "PENDIENTE_ASIGNAR"
                            colocadas_m += 1

            if not es_inf and ses_t > 0:
                franjas_t = ordenar_franjas_por_prioridad(franjas_t_pri, prio_franja)
                colocadas_t = 0
                for f in franjas_t:
                    for d in dias_validos:
                        if colocadas_t < ses_t:
                            aula_libre = (datos["horarios_aula"][nom_aula][f][d] == tutor)
                            esp_libre = (datos["horarios_esp"][id_esp][f][d] == "Disponible / Apoyo")
                            if aula_libre and esp_libre:
                                datos["horarios_aula"][nom_aula][f][d] = id_esp
                                datos["horarios_esp"][id_esp][f][d] = f"Aula: {nom_aula}"
                                datos["horarios_tutor"][nom_aula][f][d] = "PENDIENTE_ASIGNAR"
                                colocadas_t += 1

    for a in datos["aulas"]:
        nom_aula = a["aula"]
        ciclo_actual = a.get("ciclo", "Primaria")
        proyectos_tutor = a.get("proyectos", [])
        if not proyectos_tutor and a.get("coord"):
            proyectos_tutor = ["Coordinador/a de Ciclo"]
        horas_proy_max = a.get("horas_proyectos", 1 if a.get("coord") else 0)
        etiqueta_proy = ", ".join(proyectos_tutor) if proyectos_tutor else "Proyecto/Cargo"

        companeros = [x["aula"] for x in datos["aulas"] if x.get("ciclo") == ciclo_actual and x["aula"] != nom_aula]
        aula_refuerzo = companeros[0] if companeros else "Su Ciclo"

        h_plan = 0
        h_coord = 0
        h_proy = 0

        for f, dias_dict in datos["horarios_tutor"][nom_aula].items():
            for d in DIAS:
                if dias_dict[d] == "PENDIENTE_ASIGNAR":
                    if h_plan < 1:
                        datos["horarios_tutor"][nom_aula][f][d] = "LIBRE: Planificación"
                        h_plan += 1
                    elif h_coord < 1:
                        datos["horarios_tutor"][nom_aula][f][d] = "LIBRE: Coordinación"
                        h_coord += 1
                    elif h_proy < horas_proy_max:
                        datos["horarios_tutor"][nom_aula][f][d] = f"LIBRE: {etiqueta_proy}"
                        h_proy += 1
                    else:
                        datos["horarios_tutor"][nom_aula][f][d] = f"APOYO / REFUERZO en {aula_refuerzo}"

    for e in datos["especialistas"]:
        id_esp = f"{e['nombre']} ({e['area']})"
        matriz = datos["horarios_esp"].get(id_esp, {})
        proyectos_esp = e.get("proyectos", [])
        horas_proy_esp = e.get("horas_proyectos", 0)
        etiqueta_proy_esp = ", ".join(proyectos_esp) if proyectos_esp else "Proyecto/Cargo"

        h_p, h_c, h_pr = 0, 0, 0
        for f, dias_dict in matriz.items():
            for d in DIAS:
                if dias_dict[d] == "Disponible / Apoyo":
                    if h_p < 1:
                        datos["horarios_esp"][id_esp][f][d] = "LIBRE: Planificación"
                        h_p += 1
                    elif h_c < 1:
                        datos["horarios_esp"][id_esp][f][d] = "LIBRE: Coordinación"
                        h_c += 1
                    elif h_pr < horas_proy_esp:
                        datos["horarios_esp"][id_esp][f][d] = f"LIBRE: {etiqueta_proy_esp}"
                        h_pr += 1

    guardar_datos(datos)

def renderizar_tabla_html(matriz, tutor_base=""):
    html = '<table class="tabla-horario"><thead><tr><th>Franja Horaria</th>'
    for d in DIAS:
        html += f'<th>{d}</th>'
    html += '</tr></thead><tbody>'

    for f, dias_dict in matriz.items():
        if "Recreo" in f or "Almuerzo" in f:
            html += f'<tr class="recreo-row"><td><b>{f}</b></td>' + "".join([f'<td>{dias_dict[d]}</td>' for d in DIAS]) + '</tr>'
        else:
            html += f'<tr><td><b>{f}</b></td>'
            for d in DIAS:
                val = dias_dict.get(d, "")
                clase = ""
                if "LIBRE" in val:
                    clase = 'class="celda-libre"'
                elif "APOYO" in val or "Disponible" in val:
                    clase = 'class="celda-apoyo"'
                elif tutor_base and val != tutor_base and "En su aula" not in val:
                    clase = 'class="celda-esp"'
                html += f'<td {clase}>{val}</td>'
            html += '</tr>'
    html += '</tbody></table>'
    return html

def generar_documento_imprimible():
    html_doc = """<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Horarios Completos del Centro - Palantir School</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; color: #1e293b; }
            h1 { color: #1F4E79; text-align: center; margin-bottom: 5px; }
            h2 { color: #1F4E79; border-bottom: 2px solid #1F4E79; padding-bottom: 4px; margin-top: 20px; font-size: 18px; }
            h3 { color: #2F5597; margin-top: 14px; margin-bottom: 6px; font-size: 15px; }
            .btn-print { display: block; margin: 15px auto; padding: 12px 24px; background: #1F4E79; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
            .tabla-horario { width: 100%; border-collapse: collapse; margin-top: 6px; margin-bottom: 16px; font-size: 12px; }
            .tabla-horario th { background-color: #1F4E79 !important; color: white !important; padding: 8px; text-align: center; border: 1px solid #94a3b8; width: 16%; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .tabla-horario td { padding: 8px; text-align: center; border: 1px solid #94a3b8; background-color: #ffffff; }
            .celda-esp { background-color: #e0f2fe !important; font-weight: bold; color: #0369a1 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .celda-apoyo { background-color: #fef3c7 !important; font-weight: bold; color: #b45309 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .celda-libre { background-color: #dcfce7 !important; font-weight: bold; color: #15803d !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .recreo-row td { background-color: #f1f5f9 !important; font-weight: bold; color: #64748b !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .page-break { page-break-after: always; }
            @media print { .no-print { display: none; } }
        </style>
    </head>
    <body onload="window.print()">
        <div class="no-print">
            <button class="btn-print" onclick="window.print()">🖨️ Imprimir o Guardar como PDF ahora</button>
        </div>
        <h1>📅 Cuadrante General de Horarios del Centro</h1>
    """

    for a in datos["aulas"]:
        nom_aula = a["aula"]
        tutor_nom = a["tutor"]
        matriz_aula = datos["horarios_aula"].get(nom_aula, {})
        matriz_tut = datos["horarios_tutor"].get(nom_aula, {})

        html_doc += '<div class="page-break">'
        html_doc += f'<h2>🏫 Aula: {nom_aula} ({a.get("nivel", "")})</h2>'
        html_doc += f'<h3>Horario del Grupo (Profesionales en el aula)</h3>'
        html_doc += renderizar_tabla_html(matriz_aula, tutor_base=tutor_nom)
        html_doc += f'<h3>👤 Horario Individual del Tutor: {tutor_nom}</h3>'
        html_doc += renderizar_tabla_html(matriz_tut, tutor_base=tutor_nom)
        html_doc += '</div>'

    for e in datos["especialistas"]:
        id_esp = f"{e['nombre']} ({e['area']})"
        matriz_e = datos["horarios_esp"].get(id_esp, {})
        html_doc += '<div class="page-break">'
        html_doc += f'<h2>👤 Especialista / Apoyo: {id_esp}</h2>'
        html_doc += renderizar_tabla_html(matriz_e, tutor_base="Disponible / Apoyo")
        html_doc += '</div>'

    html_doc += "</body></html>"
    return html_doc

# ==========================================
# PANTALLA 1: CONFIGURACIÓN INICIAL
# ==========================================
if not datos["config_guardada"]:
    st.markdown('<div class="main-header">⚙️ Configuración Inicial del Centro (Modo Anónimo)</div>', unsafe_allow_html=True)
    st.write("Registra las aulas con sus tutores, coordinaciones de proyectos y especialistas con sus cursos y franjas prioritarias.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sub-header">🏫 1. Aulas, Tutores y Coordinaciones</div>', unsafe_allow_html=True)
        with st.container():
            c1, c2 = st.columns(2)
            nivel_sel = c1.selectbox("Curso / Nivel del Aula:", LISTA_CURSOS)
            nom_aula = c2.text_input("Nombre/Alias del Aula (ej. 1ºA, 3 Años):", value=nivel_sel)

            nom_tutor = st.text_input("Identificador del Tutor (ej. Tutor 1, Docente A):")

            c3, c4 = st.columns([0.65, 0.35])
            proy_tutor = c3.multiselect("Coordinaciones / Proyectos (Generan libranza):", LISTA_PROYECTOS, key="proy_tut")
            horas_lib_tutor = c4.number_input(
                "Horas extra libranza:", min_value=0, max_value=10,
                value=1 if proy_tutor else 0,
                help="Horas adicionales a las 2h base de Planificación y Coordinación"
            )

            if st.button("➕ Registrar Aula y Tutor"):
                if nom_aula and nom_tutor:
                    if "Infantil" in nivel_sel: ciclo = "Infantil"
                    elif nivel_sel in ["1º Primaria", "2º Primaria"]: ciclo = "1º Ciclo Primaria"
                    elif nivel_sel in ["3º Primaria", "4º Primaria"]: ciclo = "2º Ciclo Primaria"
                    else: ciclo = "3º Ciclo Primaria"

                    datos["aulas"].append({
                        "aula": nom_aula,
                        "tutor": nom_tutor,
                        "nivel": nivel_sel,
                        "ciclo": ciclo,
                        "proyectos": proy_tutor,
                        "horas_proyectos": horas_lib_tutor,
                        "coord": ("Coordinador/a de Ciclo" in proy_tutor)
                    })
                    guardar_datos(datos)
                    st.rerun()

        for i, a in enumerate(datos["aulas"]):
            ca, cb = st.columns([0.85, 0.15])
            proys = a.get("proyectos", ["Coord. Ciclo"] if a.get("coord") else [])
            h_ext = a.get("horas_proyectos", 1 if a.get("coord") else 0)
            txt_proy = f" | ⭐ {', '.join(proys)} (+{h_ext}h lib.)" if proys else " | (2h base)"
            ca.write(f"• **{a['aula']}** [{a.get('nivel', '')}] — Tutor: `{a['tutor']}`{txt_proy}")
            if cb.button("❌", key=f"del_a_{i}"):
                datos["aulas"].pop(i)
                guardar_datos(datos)
                st.rerun()

    with col2:
        st.markdown('<div class="sub-header">👥 2. Especialistas, Cursos y Franja Prioritaria</div>', unsafe_allow_html=True)
        with st.container():
            ce1, ce2 = st.columns(2)
            nom_esp = ce1.text_input("Identificador Especialista (ej. Esp. Inglés 1, EF 1):")
            area_esp = ce2.selectbox("Especialidad:", [
                "Inglés", "Educación Física (EF)", "Música / Artística", "Religión",
                "PT (Pedagogía Terapéutica)", "AL (Audición y Lenguaje)", "PROA+ / Apoyo", "Apoyo Infantil"
            ])

            cursos_esp = st.multiselect(
                "Cursos preferentes que atiende:",
                ["Todos los cursos"] + LISTA_CURSOS,
                default=["Todos los cursos"]
            )

            franja_prio = st.selectbox(
                "Franja horaria prioritaria para sus clases:",
                OPCIONES_FRANJA_PRIORITARIA
            )

            ce3, ce4 = st.columns([0.65, 0.35])
            proy_esp = ce3.multiselect("Coordinaciones / Proyectos del Especialista:", LISTA_PROYECTOS, key="proy_esp")
            horas_lib_esp = ce4.number_input(
                "Horas extra libranza (Esp.):", min_value=0, max_value=10,
                value=1 if proy_esp else 0
            )

            if st.button("➕ Registrar Especialista"):
                if nom_esp:
                    datos["especialistas"].append({
                        "nombre": nom_esp,
                        "area": area_esp,
                        "cursos": cursos_esp if cursos_esp else ["Todos los cursos"],
                        "franja_prioritaria": franja_prio,
                        "proyectos": proy_esp,
                        "horas_proyectos": horas_lib_esp
                    })
                    guardar_datos(datos)
                    st.rerun()

        for i, e in enumerate(datos["especialistas"]):
            ca, cb = st.columns([0.85, 0.15])
            cursos_txt = ", ".join(e.get("cursos", [e.get("etapa", "Todos")]))
            franja_txt = e.get("franja_prioritaria", "Sin preferencia")
            proys_e = e.get("proyectos", [])
            h_ext_e = e.get("horas_proyectos", 0)
            txt_proy_e = f" | ⭐ {', '.join(proys_e)} (+{h_ext_e}h)" if proys_e else ""
            ca.write(f"• **{e['nombre']}** (`{e['area']}`) — Cursos: *{cursos_txt}* | Prioridad: `{franja_txt}`{txt_proy_e}")
            if cb.button("❌", key=f"del_e_{i}"):
                datos["especialistas"].pop(i)
                guardar_datos(datos)
                st.rerun()

    st.markdown("---")
    if st.button("💾 Guardar y Pasar al Panel de Horarios", type="primary"):
        if not datos["aulas"] and not datos["especialistas"]:
            st.warning("Añade al menos un aula y un especialista antes de continuar.")
        else:
            if not datos.get("horarios_aula"):
                autogenerar_cuadrante()
            datos["config_guardada"] = True
            guardar_datos(datos)
            st.rerun()

# ==========================================
# PANTALLA 2: PANEL DE HORARIOS (CUADRÍCULA 3xN)
# ==========================================
else:
    c_top1, c_top2, c_top3, c_top4 = st.columns([0.40, 0.22, 0.20, 0.18])
    with c_top1:
        st.markdown('<div class="main-header">📅 Panel de Horarios - Sistema Palantir</div>', unsafe_allow_html=True)
    with c_top2:
        if st.button("⚡ Autogenerar Cuadrante Completo", type="primary"):
            autogenerar_cuadrante()
            st.toast("Horarios generados aplicando cursos, franjas prioritarias y libranzas de proyectos", icon="✅")
            st.rerun()
    with c_top3:
        st.download_button(
            label="🖨️ Imprimir Todos",
            data=generar_documento_imprimible(),
            file_name="Horarios_Completos_Imprimir.html",
            mime="text/html"
        )
    with c_top4:
        if st.button("⚙️ Configurar Personal/Aulas"):
            datos["config_guardada"] = False
            st.session_state.vista_detalle = None
            guardar_datos(datos)
            st.rerun()

    if st.session_state.vista_detalle:
        sel = st.session_state.vista_detalle
        tipo = st.session_state.tipo_detalle

        if st.button("⬅️ Volver a la Cuadrícula de Aulas y Especialistas"):
            st.session_state.vista_detalle = None
            st.rerun()

        if tipo == "AULA":
            info_aula = next((x for x in datos["aulas"] if x["aula"] == sel), None)
            tutor_nom = info_aula["tutor"] if info_aula else "Tutor"

            st.markdown(f'<div class="sub-header">🏫 Horario del Grupo: {sel} (Profesionales en el aula)</div>', unsafe_allow_html=True)
            st.caption("En azul se destacan las sesiones impartidas por Especialistas (sin indicar asignatura, solo el profesional presente).")
            matriz_aula = datos["horarios_aula"].get(sel, {})
            st.markdown(renderizar_tabla_html(matriz_aula, tutor_base=tutor_nom), unsafe_allow_html=True)

            st.markdown(f'<div class="sub-header">👤 Horario Individual del Tutor: {tutor_nom}</div>', unsafe_allow_html=True)
            st.caption("Incluye sus horas de Planificación, Coordinación, Libranzas por Proyectos y Apoyo/Refuerzo en su ciclo.")
            matriz_tut = datos["horarios_tutor"].get(sel, {})
            st.markdown(renderizar_tabla_html(matriz_tut, tutor_base=tutor_nom), unsafe_allow_html=True)

            with st.expander("✏️ Modificar manualmente una sesión de este horario"):
                col_a, col_b, col_c, col_d = st.columns(4)
                f_mod = col_a.selectbox("Franja:", [f for f in matriz_aula.keys() if "Recreo" not in f and "Almuerzo" not in f])
                d_mod = col_b.selectbox("Día:", DIAS)
                opciones = [tutor_nom] + [f"{e['nombre']} ({e['area']})" for e in datos["especialistas"]]
                p_mod = col_c.selectbox("Profesional en el aula:", opciones)
                t_mod = col_d.text_input("Tarea del tutor en esa hora:", value="APOYO / REFUERZO en Ciclo")
                if st.button("Guardar cambio manual"):
                    datos["horarios_aula"][sel][f_mod][d_mod] = p_mod
                    datos["horarios_tutor"][sel][f_mod][d_mod] = f"En su aula ({sel})" if p_mod == tutor_nom else t_mod
                    guardar_datos(datos)
                    st.rerun()

        elif tipo == "ESP":
            st.markdown(f'<div class="sub-header">👤 Horario del Especialista / Apoyo: {sel}</div>', unsafe_allow_html=True)
            st.caption("Indica en qué aula imparte docencia, sus horas de liberación (Planificación/Coordinación/Proyectos) y horas disponibles de apoyo.")
            matriz_e = datos["horarios_esp"].get(sel, {})
            st.markdown(renderizar_tabla_html(matriz_e, tutor_base="Disponible / Apoyo"), unsafe_allow_html=True)

            with st.expander("✏️ Asignar manualmente aula o apoyo a este especialista"):
                col_a, col_b, col_c = st.columns(3)
                f_mod = col_a.selectbox("Franja:", [f for f in matriz_e.keys() if "Recreo" not in f])
                d_mod = col_b.selectbox("Día:", DIAS)
                destinos = ["Disponible / Apoyo", "LIBRE: Planificación", "LIBRE: Coordinación", "LIBRE: Coordinación Proyecto"] + [f"Aula: {a['aula']}" for a in datos["aulas"]]
                dest_mod = col_c.selectbox("Asignación:", destinos)
                if st.button("Actualizar sesión del especialista"):
                    datos["horarios_esp"][sel][f_mod][d_mod] = dest_mod
                    guardar_datos(datos)
                    st.rerun()

    else:
        st.markdown('<div class="sub-header">📚 Aulas del Centro (Cuadrícula de 3 Columnas)</div>', unsafe_allow_html=True)
        aulas = datos["aulas"]
        if aulas:
            for i in range(0, len(aulas), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(aulas):
                        a = aulas[i + j]
                        etiqueta = f"🏫 {a['aula']} — {a['tutor']}"
                        with cols[j]:
                            if st.button(etiqueta, key=f"btn_aula_{i+j}"):
                                st.session_state.vista_detalle = a["aula"]
                                st.session_state.tipo_detalle = "AULA"
                                st.rerun()
        else:
            st.info("No hay aulas registradas.")

        st.markdown("---")
        st.markdown('<div class="sub-header">👥 Horarios de Especialistas y Apoyos</div>', unsafe_allow_html=True)
        especialistas = datos["especialistas"]
        if especialistas:
            for i in range(0, len(especialistas), 3):
                cols_e = st.columns(3)
                for j in range(3):
                    if i + j < len(especialistas):
                        e = especialistas[i + j]
                        id_esp = f"{e['nombre']} ({e['area']})"
                        with cols_e[j]:
                            if st.button(f"👤 {id_esp}", key=f"btn_esp_{i+j}"):
                                st.session_state.vista_detalle = id_esp
                                st.session_state.tipo_detalle = "ESP"
                                st.rerun()
        else:
            st.info("No hay especialistas registrados.")