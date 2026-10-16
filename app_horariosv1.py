<<<<<<< HEAD
import streamlit as st
import json
import os

st.set_page_config(page_title="Gestor de Horarios - Palantir School", layout="wide")

ARCHIVO_DATOS = "datos_centro.json"

# ==========================================
# FUNCIONES DE GUARDADO Y CARGA PERMANENTE
# ==========================================
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "config_guardada": False,
        "aulas": [],          # Lista de dicts: {"nombre": "1º Primaria", "tutor": "Tutor 1", "ciclo": "1º Ciclo", "coord": True}
        "especialistas": [],  # Lista de dicts: {"nombre": "Esp. Inglés 1", "area": "Inglés"}
        "horarios": {}        # Diccionario con las matrices de horarios por aula/especialista
    }

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()

if "vista_detalle" not in st.session_state:
    st.session_state.vista_detalle = None

datos = st.session_state.datos

# Estilos CSS modernos
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: 700; color: #1F4E79; margin-bottom: 15px; }
    .sub-header { font-size: 20px; font-weight: 600; color: #2F5597; margin-top: 15px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; height: 45px; }
    .tabla-horario { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; }
    .tabla-horario th { background-color: #1F4E79; color: white; padding: 10px; text-align: center; border: 1px solid #ddd; }
    .tabla-horario td { padding: 10px; text-align: center; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: 500; }
    .recreo-row td { background-color: #D9E1F2 !important; font-weight: bold; color: #1F4E79; }
    </style>
""", unsafe_allow_html=True)

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
franjas_primaria = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 12:30 (Recreo)", "12:30 - 13:15", "13:15 - 14:00"]
franjas_infantil = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 11:30 (Recreo)", "11:30 - 12:00 (Desayuno)", "12:00 - 12:30", "12:30 - 13:15", "13:15 - 14:00"]

def inicializar_horario_si_no_existe(identificador, es_infantil=False):
    if identificador not in datos["horarios"]:
        franjas = franjas_infantil if es_infantil else franjas_primaria
        matriz = {}
        for f in franjas:
            if "Recreo" in f or "Desayuno" in f:
                matriz[f] = {d: "RECREO / DESAYUNO" for d in dias_semana}
            else:
                matriz[f] = {d: identificador for d in dias_semana}
        datos["horarios"][identificador] = matriz
        guardar_datos(datos)

# ==========================================
# PANTALLA 1: CONFIGURACIÓN INICIAL (ESTABLE)
# ==========================================
if not datos["config_guardada"]:
    st.markdown('<div class="main-header">⚙️ Configuración Inicial del Centro (Modo Anónimo)</div>', unsafe_allow_html=True)
    st.write("Introduce las aulas con sus tutores y los especialistas. Estos datos quedarán guardados en el ordenador de forma permanente.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sub-header">🏫 Aulas y Tutores</div>', unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2 = st.columns(2)
            nombre_aula = c1.text_input("Nombre del Aula (ej. 2º Primaria, 3 Años):")
            nombre_tutor = c2.text_input("Identificador Tutor (ej. Tutor 2º, Arita):")
            
            c3, c4 = st.columns(2)
            etapa_ciclo = c3.selectbox("Etapa / Ciclo:", ["Infantil", "1º Ciclo Primaria (1º-2º)", "2º Ciclo Primaria (3º-4º)", "3º Ciclo Primaria (5º-6º)"])
            es_coord = c4.checkbox("¿Es Coordinador de Ciclo? (3h libres)")

            if st.button("➕ Añadir Aula y Tutor"):
                if nombre_aula and nombre_tutor:
                    nuevo = {"aula": nombre_aula, "tutor": nombre_tutor, "ciclo": etapa_ciclo, "coord": es_coord}
                    datos["aulas"].append(nuevo)
                    inicializar_horario_si_no_existe(nombre_aula, es_infantil=(etapa_ciclo == "Infantil"))
                    guardar_datos(datos)
                    st.rerun()

        st.write("**Aulas registradas:**")
        if datos["aulas"]:
            for i, a in enumerate(datos["aulas"]):
                ca, cb = st.columns([0.85, 0.15])
                coord_txt = " ⭐ (Coord. Ciclo - 3h)" if a["coord"] else " (2h libres)"
                ca.write(f"• **{a['aula']}** — Tutor: `{a['tutor']}` | *{a['ciclo']}*{coord_txt}")
                if cb.button("❌", key=f"del_a_{i}"):
                    datos["aulas"].pop(i)
                    guardar_datos(datos)
                    st.rerun()
        else:
            st.info("No hay aulas añadidas todavía.")

    with col2:
        st.markdown('<div class="sub-header">👥 Especialistas y Apoyos</div>', unsafe_allow_html=True)
        with st.container(border=True):
            ce1, ce2 = st.columns(2)
            nombre_esp = ce1.text_input("Identificador Especialista (ej. Esp. Inglés 1):")
            area_esp = ce2.selectbox("Especialidad / Rol:", ["Inglés", "Educación Física (EF)", "Música / Artística", "Religión", "PT (Pedagogía Terapéutica)", "AL (Audición y Lenguaje)", "PROA+ / Apoyo", "Apoyo Infantil"])

            if st.button("➕ Añadir Especialista"):
                if nombre_esp:
                    nuevo_e = {"nombre": nombre_esp, "area": area_esp}
                    datos["especialistas"].append(nuevo_e)
                    inicializar_horario_si_no_existe(f"{nombre_esp} ({area_esp})", es_infantil=False)
                    guardar_datos(datos)
                    st.rerun()

        st.write("**Especialistas registrados:**")
        if datos["especialistas"]:
            for i, e in enumerate(datos["especialistas"]):
                ca, cb = st.columns([0.85, 0.15])
                ca.write(f"• **{e['nombre']}** — Especialidad: `{e['area']}`")
                if cb.button("❌", key=f"del_e_{i}"):
                    datos["especialistas"].pop(i)
                    guardar_datos(datos)
                    st.rerun()
        else:
            st.info("No hay especialistas añadidos todavía.")

    st.markdown("---")
    if st.button("💾 Guardar Configuración y Acceder al Panel de Horarios", type="primary"):
        if not datos["aulas"] and not datos["especialistas"]:
            st.warning("Introduce al menos un aula o un especialista para continuar.")
        else:
            datos["config_guardada"] = True
            guardar_datos(datos)
            st.rerun()

# ==========================================
# PANTALLA 2: PANEL DE HORARIOS (3 COLUMNAS)
# ==========================================
else:
    col_t1, col_t2 = st.columns([0.8, 0.2])
    with col_t1:
        st.markdown('<div class="main-header">📅 Panel de Gestión de Horarios del Centro</div>', unsafe_allow_html=True)
    with col_t2:
        if st.button("⚙️ Modificar Profesionales/Aulas"):
            datos["config_guardada"] = False
            st.session_state.vista_detalle = None
            guardar_datos(datos)
            st.rerun()

    # VISTA DETALLADA DE UN HORARIO CONCRETO
    if st.session_state.vista_detalle:
        seleccion = st.session_state.vista_detalle
        if st.button("⬅️ Volver a la Cuadrícula General"):
            st.session_state.vista_detalle = None
            st.rerun()

        st.markdown(f'<div class="sub-header">Horario de: {seleccion} (Solo Profesionales)</div>', unsafe_allow_html=True)
        
        # Lista de todos los profesionales disponibles para asignar en celdas
        lista_profes = ["RECREO / DESAYUNO", "LIBRE / PLANIFICACIÓN", "COORDINACIÓN"]
        lista_profes += [f"{a['tutor']} (Tutor {a['aula']})" for a in datos["aulas"]]
        lista_profes += [f"{e['nombre']} ({e['area']})" for e in datos["especialistas"]]

        matriz_actual = datos["horarios"].get(seleccion, {})

        # Editor rápido de celdas
        with st.expander("✏️ Asignar o cambiar profesor en una hora concreta"):
            c_f, c_d, c_p, c_b = st.columns([0.25, 0.25, 0.35, 0.15])
            franja_sel = c_f.selectbox("Franja Horaria:", list(matriz_actual.keys()))
            dia_sel = c_d.selectbox("Día:", dias_semana)
            profe_sel = c_p.selectbox("Profesional presente:", lista_profes)
            if c_b.button("Aplicar"):
                datos["horarios"][seleccion][franja_sel][dia_sel] = profe_sel
                guardar_datos(datos)
                st.rerun()

        # Renderizar tabla HTML limpia sin depender de Pandas/Numpy
        html_table = '<table class="tabla-horario"><thead><tr><th>Franja Horaria</th>'
        for d in dias_semana:
            html_table += f'<th>{d}</th>'
        html_table += '</tr></thead><tbody>'

        for franja, dias_dict in matriz_actual.items():
            es_recreo = "Recreo" in franja or "Desayuno" in franja
            clase_fila = 'class="recreo-row"' if es_recreo else ''
            html_table += f'<tr {clase_fila}><td><b>{franja}</b></td>'
            for d in dias_semana:
                valor = dias_dict.get(d, "")
                html_table += f'<td>{valor}</td>'
            html_table += '</tr>'
        html_table += '</tbody></table>'

        st.markdown(html_table, unsafe_allow_html=True)

    # VISTA DE CUADRÍCULA (3 COLUMNAS)
    else:
        st.markdown('<div class="sub-header">📚 Horarios por Aula (Cuadrícula de 3 Columnas)</div>', unsafe_allow_html=True)
        aulas = datos["aulas"]
        if aulas:
            for i in range(0, len(aulas), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(aulas):
                        item = aulas[i + j]
                        nombre_boton = f"🏫 {item['aula']} (Tutor: {item['tutor']})"
                        with cols[j]:
                            if st.button(nombre_boton, key=f"btn_aula_{i+j}"):
                                inicializar_horario_si_no_existe(item["aula"], es_infantil=(item["ciclo"] == "Infantil"))
                                st.session_state.vista_detalle = item["aula"]
                                st.rerun()
        else:
            st.info("No hay aulas configuradas.")

        st.markdown("---")
        st.markdown('<div class="sub-header">👥 Horarios de Especialistas y Apoyos</div>', unsafe_allow_html=True)
        especialistas = datos["especialistas"]
        if especialistas:
            for i in range(0, len(especialistas), 3):
                cols_e = st.columns(3)
                for j in range(3):
                    if i + j < len(especialistas):
                        esp = especialistas[i + j]
                        id_esp = f"{esp['nombre']} ({esp['area']})"
                        with cols_e[j]:
                            if st.button(f"👤 {id_esp}", key=f"btn_esp_{i+j}"):
                                inicializar_horario_si_no_existe(id_esp, es_infantil=False)
                                st.session_state.vista_detalle = id_esp
                                st.rerun()
        else:
=======
import streamlit as st
import json
import os

st.set_page_config(page_title="Gestor de Horarios - Palantir School", layout="wide")

ARCHIVO_DATOS = "datos_centro.json"

# ==========================================
# FUNCIONES DE GUARDADO Y CARGA PERMANENTE
# ==========================================
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "config_guardada": False,
        "aulas": [],          # Lista de dicts: {"nombre": "1º Primaria", "tutor": "Tutor 1", "ciclo": "1º Ciclo", "coord": True}
        "especialistas": [],  # Lista de dicts: {"nombre": "Esp. Inglés 1", "area": "Inglés"}
        "horarios": {}        # Diccionario con las matrices de horarios por aula/especialista
    }

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

if "datos" not in st.session_state:
    st.session_state.datos = cargar_datos()

if "vista_detalle" not in st.session_state:
    st.session_state.vista_detalle = None

datos = st.session_state.datos

# Estilos CSS modernos
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: 700; color: #1F4E79; margin-bottom: 15px; }
    .sub-header { font-size: 20px; font-weight: 600; color: #2F5597; margin-top: 15px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; height: 45px; }
    .tabla-horario { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; }
    .tabla-horario th { background-color: #1F4E79; color: white; padding: 10px; text-align: center; border: 1px solid #ddd; }
    .tabla-horario td { padding: 10px; text-align: center; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: 500; }
    .recreo-row td { background-color: #D9E1F2 !important; font-weight: bold; color: #1F4E79; }
    </style>
""", unsafe_allow_html=True)

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
franjas_primaria = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 12:30 (Recreo)", "12:30 - 13:15", "13:15 - 14:00"]
franjas_infantil = ["9:00 - 10:00", "10:00 - 11:00", "11:00 - 11:30 (Recreo)", "11:30 - 12:00 (Desayuno)", "12:00 - 12:30", "12:30 - 13:15", "13:15 - 14:00"]

def inicializar_horario_si_no_existe(identificador, es_infantil=False):
    if identificador not in datos["horarios"]:
        franjas = franjas_infantil if es_infantil else franjas_primaria
        matriz = {}
        for f in franjas:
            if "Recreo" in f or "Desayuno" in f:
                matriz[f] = {d: "RECREO / DESAYUNO" for d in dias_semana}
            else:
                matriz[f] = {d: identificador for d in dias_semana}
        datos["horarios"][identificador] = matriz
        guardar_datos(datos)

# ==========================================
# PANTALLA 1: CONFIGURACIÓN INICIAL (ESTABLE)
# ==========================================
if not datos["config_guardada"]:
    st.markdown('<div class="main-header">⚙️ Configuración Inicial del Centro (Modo Anónimo)</div>', unsafe_allow_html=True)
    st.write("Introduce las aulas con sus tutores y los especialistas. Estos datos quedarán guardados en el ordenador de forma permanente.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sub-header">🏫 Aulas y Tutores</div>', unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2 = st.columns(2)
            nombre_aula = c1.text_input("Nombre del Aula (ej. 2º Primaria, 3 Años):")
            nombre_tutor = c2.text_input("Identificador Tutor (ej. Tutor 2º, Arita):")
            
            c3, c4 = st.columns(2)
            etapa_ciclo = c3.selectbox("Etapa / Ciclo:", ["Infantil", "1º Ciclo Primaria (1º-2º)", "2º Ciclo Primaria (3º-4º)", "3º Ciclo Primaria (5º-6º)"])
            es_coord = c4.checkbox("¿Es Coordinador de Ciclo? (3h libres)")

            if st.button("➕ Añadir Aula y Tutor"):
                if nombre_aula and nombre_tutor:
                    nuevo = {"aula": nombre_aula, "tutor": nombre_tutor, "ciclo": etapa_ciclo, "coord": es_coord}
                    datos["aulas"].append(nuevo)
                    inicializar_horario_si_no_existe(nombre_aula, es_infantil=(etapa_ciclo == "Infantil"))
                    guardar_datos(datos)
                    st.rerun()

        st.write("**Aulas registradas:**")
        if datos["aulas"]:
            for i, a in enumerate(datos["aulas"]):
                ca, cb = st.columns([0.85, 0.15])
                coord_txt = " ⭐ (Coord. Ciclo - 3h)" if a["coord"] else " (2h libres)"
                ca.write(f"• **{a['aula']}** — Tutor: `{a['tutor']}` | *{a['ciclo']}*{coord_txt}")
                if cb.button("❌", key=f"del_a_{i}"):
                    datos["aulas"].pop(i)
                    guardar_datos(datos)
                    st.rerun()
        else:
            st.info("No hay aulas añadidas todavía.")

    with col2:
        st.markdown('<div class="sub-header">👥 Especialistas y Apoyos</div>', unsafe_allow_html=True)
        with st.container(border=True):
            ce1, ce2 = st.columns(2)
            nombre_esp = ce1.text_input("Identificador Especialista (ej. Esp. Inglés 1):")
            area_esp = ce2.selectbox("Especialidad / Rol:", ["Inglés", "Educación Física (EF)", "Música / Artística", "Religión", "PT (Pedagogía Terapéutica)", "AL (Audición y Lenguaje)", "PROA+ / Apoyo", "Apoyo Infantil"])

            if st.button("➕ Añadir Especialista"):
                if nombre_esp:
                    nuevo_e = {"nombre": nombre_esp, "area": area_esp}
                    datos["especialistas"].append(nuevo_e)
                    inicializar_horario_si_no_existe(f"{nombre_esp} ({area_esp})", es_infantil=False)
                    guardar_datos(datos)
                    st.rerun()

        st.write("**Especialistas registrados:**")
        if datos["especialistas"]:
            for i, e in enumerate(datos["especialistas"]):
                ca, cb = st.columns([0.85, 0.15])
                ca.write(f"• **{e['nombre']}** — Especialidad: `{e['area']}`")
                if cb.button("❌", key=f"del_e_{i}"):
                    datos["especialistas"].pop(i)
                    guardar_datos(datos)
                    st.rerun()
        else:
            st.info("No hay especialistas añadidos todavía.")

    st.markdown("---")
    if st.button("💾 Guardar Configuración y Acceder al Panel de Horarios", type="primary"):
        if not datos["aulas"] and not datos["especialistas"]:
            st.warning("Introduce al menos un aula o un especialista para continuar.")
        else:
            datos["config_guardada"] = True
            guardar_datos(datos)
            st.rerun()

# ==========================================
# PANTALLA 2: PANEL DE HORARIOS (3 COLUMNAS)
# ==========================================
else:
    col_t1, col_t2 = st.columns([0.8, 0.2])
    with col_t1:
        st.markdown('<div class="main-header">📅 Panel de Gestión de Horarios del Centro</div>', unsafe_allow_html=True)
    with col_t2:
        if st.button("⚙️ Modificar Profesionales/Aulas"):
            datos["config_guardada"] = False
            st.session_state.vista_detalle = None
            guardar_datos(datos)
            st.rerun()

    # VISTA DETALLADA DE UN HORARIO CONCRETO
    if st.session_state.vista_detalle:
        seleccion = st.session_state.vista_detalle
        if st.button("⬅️ Volver a la Cuadrícula General"):
            st.session_state.vista_detalle = None
            st.rerun()

        st.markdown(f'<div class="sub-header">Horario de: {seleccion} (Solo Profesionales)</div>', unsafe_allow_html=True)
        
        # Lista de todos los profesionales disponibles para asignar en celdas
        lista_profes = ["RECREO / DESAYUNO", "LIBRE / PLANIFICACIÓN", "COORDINACIÓN"]
        lista_profes += [f"{a['tutor']} (Tutor {a['aula']})" for a in datos["aulas"]]
        lista_profes += [f"{e['nombre']} ({e['area']})" for e in datos["especialistas"]]

        matriz_actual = datos["horarios"].get(seleccion, {})

        # Editor rápido de celdas
        with st.expander("✏️ Asignar o cambiar profesor en una hora concreta"):
            c_f, c_d, c_p, c_b = st.columns([0.25, 0.25, 0.35, 0.15])
            franja_sel = c_f.selectbox("Franja Horaria:", list(matriz_actual.keys()))
            dia_sel = c_d.selectbox("Día:", dias_semana)
            profe_sel = c_p.selectbox("Profesional presente:", lista_profes)
            if c_b.button("Aplicar"):
                datos["horarios"][seleccion][franja_sel][dia_sel] = profe_sel
                guardar_datos(datos)
                st.rerun()

        # Renderizar tabla HTML limpia sin depender de Pandas/Numpy
        html_table = '<table class="tabla-horario"><thead><tr><th>Franja Horaria</th>'
        for d in dias_semana:
            html_table += f'<th>{d}</th>'
        html_table += '</tr></thead><tbody>'

        for franja, dias_dict in matriz_actual.items():
            es_recreo = "Recreo" in franja or "Desayuno" in franja
            clase_fila = 'class="recreo-row"' if es_recreo else ''
            html_table += f'<tr {clase_fila}><td><b>{franja}</b></td>'
            for d in dias_semana:
                valor = dias_dict.get(d, "")
                html_table += f'<td>{valor}</td>'
            html_table += '</tr>'
        html_table += '</tbody></table>'

        st.markdown(html_table, unsafe_allow_html=True)

    # VISTA DE CUADRÍCULA (3 COLUMNAS)
    else:
        st.markdown('<div class="sub-header">📚 Horarios por Aula (Cuadrícula de 3 Columnas)</div>', unsafe_allow_html=True)
        aulas = datos["aulas"]
        if aulas:
            for i in range(0, len(aulas), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(aulas):
                        item = aulas[i + j]
                        nombre_boton = f"🏫 {item['aula']} (Tutor: {item['tutor']})"
                        with cols[j]:
                            if st.button(nombre_boton, key=f"btn_aula_{i+j}"):
                                inicializar_horario_si_no_existe(item["aula"], es_infantil=(item["ciclo"] == "Infantil"))
                                st.session_state.vista_detalle = item["aula"]
                                st.rerun()
        else:
            st.info("No hay aulas configuradas.")

        st.markdown("---")
        st.markdown('<div class="sub-header">👥 Horarios de Especialistas y Apoyos</div>', unsafe_allow_html=True)
        especialistas = datos["especialistas"]
        if especialistas:
            for i in range(0, len(especialistas), 3):
                cols_e = st.columns(3)
                for j in range(3):
                    if i + j < len(especialistas):
                        esp = especialistas[i + j]
                        id_esp = f"{esp['nombre']} ({esp['area']})"
                        with cols_e[j]:
                            if st.button(f"👤 {id_esp}", key=f"btn_esp_{i+j}"):
                                inicializar_horario_si_no_existe(id_esp, es_infantil=False)
                                st.session_state.vista_detalle = id_esp
                                st.rerun()
        else:
>>>>>>> f4fc9c0da509fbfb3a2802f3c44600db0860388c
            st.info("No hay especialistas configurados.")