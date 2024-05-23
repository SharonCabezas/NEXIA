import pandas as pd
import os
from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import pickle
import streamlit_authenticator as stauth
from streamlit import session_state as ss
from streamlit_pdf_viewer import pdf_viewer
from datetime import datetime
from streamlit_calendar import calendar
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import base64

users = pd.read_excel('usuarios.xlsx')
doctors = pd.read_excel('usuarios_doc.xlsx')

def center_image(image):
    st.image(image, use_column_width='always', output_format='auto')

def authenticate(username, password):
    user_data_patient = users.loc[users['CURP'] == username]
    if not user_data_patient.empty and user_data_patient.iloc[0]['Contraseña'] == password:
        return user_data_patient.iloc[0], 'paciente'

    user_data_doctor = doctors.loc[doctors['Cédula profesional'] == username]
    if not user_data_doctor.empty and user_data_doctor.iloc[0]['Contraseña'] == password:
        return user_data_doctor.iloc[0], 'doctor'

    return None, None

def login_page():
    image = Image.open('Logo NEXIA (1).png')
    resized_image2 = image.resize((1000, 1000))
    center_image(resized_image2)

    st.markdown(
    """
        <div style="display: flex; flex-direction: column; align-items: center;">
        <h1>Iniciar sesión</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    username = st.text_input('ID de Usuario (CURP o Cedula Profesional)')
    password = st.text_input('Contraseña', type='password')
    if st.button('Iniciar sesión'):
        user_data, user_type = authenticate(username, password)
        if user_data is not None:
            st.session_state.user_data = user_data
            st.session_state.user_type = user_type
            st.success('Inicio de sesión exitosa')
            return True
        else:
            st.error('Credenciales incorrectas')
    return False

if not st.session_state.get('authenticated', False):
    if not login_page():
        st.stop()
    else:
        st.session_state.authenticated = True
        st.experimental_rerun()

image_sidebar = Image.open('Logo NEXIA (1).png')
st.sidebar.image(image_sidebar)

user_data = st.session_state.get('user_data', None)
user_type = st.session_state.get('user_type', None)

with st.sidebar:
    if user_type == 'paciente':
        selected = option_menu(
            menu_title=None,
            options=['Pérfil', 'Agendar Cita', 'Medicamentos', 'Vacunas', 'Alergias', 'Exámenes de laboratorio', 'Ruta quirúrgica', 'Imágenes médicas', 'Registro de síntomas', 'Diagnósticos médicos'],
            icons=['person', 'book', 'capsule', 'droplet', 'flower1', 'clipboard2-pulse-fill', 'heart-pulse', 'card-image', 'check2-circle', 'activity'],
            orientation='vertical',
            menu_icon=None,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": '#84D9C1'},
            }
        )

    elif user_type == 'doctor':
        selected = option_menu(
            menu_title=None,
            options=['Doctor', 'Pacientes', 'Citas'],
            icons=['person', 'file-medical', 'calendar'],
            orientation='vertical',
            menu_icon=None,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": '#84D9C1'},
            }
        )

def insert_cita_to_excel(nombre, especialidad, dia, mes, ano, motivo):
    file_path = "BD Citas.csv"
    
    # Verificar si el archivo ya existe
    if os.path.exists(file_path):
        # Leer el archivo existente
        df = pd.read_csv(file_path)
    else:
        # Crear un nuevo DataFrame si el archivo no existe
        df = pd.DataFrame(columns=['Nombre', 'Especialidad', 'Dia', 'Mes', 'Ano', 'Motivo'])
    
    # Crear un nuevo DataFrame con la nueva cita
    new_data = pd.DataFrame([[nombre, especialidad, dia, mes, ano, motivo]], columns=['Nombre', 'Especialidad', 'Dia', 'Mes', 'Ano', 'Motivo'])
    
    # Concatenar el nuevo DataFrame con el existente
    df = pd.concat([df, new_data], ignore_index=True)
    
    # Guardar el DataFrame en el archivo de Excel
    df.to_csv(file_path, index=False)

# Función para obtener citas para un médico específico desde Excel
def get_citas_from_excel(nombre_medico):
    file_path = "BD Citas.csv"
    
    # Leer el archivo de Excel
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Filtrar las citas para el médico específico
        citas = df[df['Nombre'] == nombre_medico]
        return citas
    else:
        return pd.DataFrame(columns=['NOMBRE', 'ESPECIALIDAD', 'Dia', 'Mes', 'Ano', 'MOTIVODECITA'])
        
if 'cita_agendada' not in st.session_state:
    st.session_state['cita_agendada'] = False

if st.session_state['cita_agendada']:
    st.success("¡Gracias por hacer tu cita!")
    st.write("Aquí están los detalles de tu cita:")
    st.write(f"Médico: {st.session_state['NOMBRE']}")
    st.write(f"Especialidad: {st.session_state['ESPECIALIDAD']}")
    st.write(f"Fecha: {st.session_state['dia']}/{st.session_state['mes']}/{st.session_state['ano']}")
    st.write(f"Motivo de cita: {st.session_state['MOTIVODECITA']}")
else:

    if selected == 'Agendar Cita':
        with st.form("Cita"):
            NOMBRE = st.selectbox("Médico: ", [f"{n} {ap} {am}" for n, ap, am in zip(doctors['Nombre(s)'], doctors['Apellido paterno'], doctors['Apellido materno'])])
            ESPECIALIDAD = st.selectbox("Especialidad: ", doctors['Especialidad'])
            d, m, a = st.columns(3)
            with d:
                dia = st.number_input("Día", min_value=1, max_value=31)
            with m:
                mes = st.number_input("Mes", min_value=1, max_value=12)
            with a:
                ano = st.number_input("Año", min_value=datetime.now().year, max_value=2100)
            MOTIVODECITA = st.selectbox("Motivo de cita: ", ['Primera cita', 'Seguimiento'])

            submitted = st.form_submit_button("Agendar cita")

            if submitted:
                # Guardar los datos en el estado de la sesión
                st.session_state['NOMBRE'] = NOMBRE
                st.session_state['ESPECIALIDAD'] = ESPECIALIDAD
                st.session_state['dia'] = dia
                st.session_state['mes'] = mes
                st.session_state['ano'] = ano
                st.session_state['MOTIVODECITA'] = MOTIVODECITA
                st.session_state['cita_agendada'] = True

                # Insertar datos en Excel
                insert_cita_to_excel(NOMBRE, ESPECIALIDAD, dia, mes, ano, MOTIVODECITA)

                st.success("¡Gracias por hacer tu cita!")
                st.write("Aquí están los detalles de tu cita:")
                st.write(f"Médico: {NOMBRE}")
                st.write(f"Especialidad: {ESPECIALIDAD}")
                st.write(f"Fecha: {dia}/{mes}/{ano}")
                st.write(f"Motivo de cita: {MOTIVODECITA}")
    
    if selected == 'Citas':
        NOMBRE_MEDICO = st.selectbox("Seleccionar médico: ", [f"{n} {ap} {am}" for n, ap, am in zip(doctors['Nombre(s)'], doctors['Apellido paterno'], doctors['Apellido materno'])])
        if st.button("Ver citas"):
            citas = get_citas_from_excel(NOMBRE_MEDICO)
            for index, cita in citas.iterrows():
                st.write(f"Médico: {cita['Nombre']}")
                st.write(f"Especialidad: {cita['Especialidad']}")
                st.write(f"Fecha: {cita['Dia']}/{cita['Mes']}/{cita['Ano']}")
                st.write(f"Motivo de cita: {cita['Motivo']}")
                st.write("---")

if selected == 'Pérfil':
    usuarios_pacientes = pd.read_excel("usuarios.xlsx")
    selected = st.session_state.get('selected',None)
    st.title(f'Pérfil')
    patient_data = st.session_state.get('user_data',None)

    if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:

        nombre = patient_info['Nombre(s)'].iloc[0]
        ap_paterno = patient_info['Apellido paterno'].iloc[0]
        ap_materno = patient_info['Apellido materno'].iloc[0]
        id = patient_info['ID'].iloc[0]

        st.subheader(f'Bienvenido, {nombre} {ap_paterno} {ap_materno} {id}')
        col1, col2, col3 = st.columns(3)

        with col2.container():
            col2.metric('Edad', user_data['Edad'])
            col2.metric("Padecimientos", user_data['Padecimientos'])
            col2.metric("Tipo de sangre", user_data['Tipo de sangre'])
            col2.metric("Altura", user_data['Altura'])
            col2.metric("Peso", user_data['Peso'])

        with col3.container():
            col3.metric('Género', user_data['Género'])
            col3.metric('Alergias', user_data['Alergias'])
            col3.metric('Medicación actual', user_data['Medicación actual'])
            col3.metric('Donante de organos', user_data['Donante de organos'])
            col3.metric('Contacto de emergencia', user_data['Contacto de emergencia'])

        try:
            path = f'{id}.jpeg'
            print("Ruta de la imagen:", path)
            image = Image.open(path)
            col1.image(image, caption=f'Paciente')

        except FileNotFoundError:
            col1.write('No hay imagen registrada.')

      with st.expander("Nombre completo"):
        st.write(f'Nombre(s): {user_data["Nombre(s)"]}')
        st.write(f'Apellido paterno: {user_data["Apellido paterno"]}')
        st.write(f'Apellido materno: {user_data["Apellido materno"]}')
        st.write(f'Género: {user_data["Género"]}')
        st.write(f'Día de nacimiento: {user_data["Día de nacimiento"]}')
        st.write(f'Mes de nacimiento: {user_data["Mes de nacimiento"]}')
        st.write(f'Año de nacimiento: {user_data["Año de nacimiento"]}')

      with st.expander("Datos generales"):
        st.write(f'Ocupación: {user_data["Ocupación"]}')
        st.write(f'Estado civil: {user_data["Estado civil"]}')
        st.write(f'Grupo étnico: {user_data["Grupo étnico"]}')
        st.write(f'Religión: {user_data["Religión"]}')
        st.write(f'Vivienda: {user_data["Vivienda"]}')

      with st.expander("Domicilio"):
        st.write(f'Calle: {user_data["Calle"]}')
        st.write(f'Número ext: {user_data["Número ext"]}')
        st.write(f'Número int: {user_data["Número int"]}')
        st.write(f'Estado: {user_data["Estado"]}')
        st.write(f'Municipio: {user_data["Municipio"]}')
        st.write(f'Colonia: {user_data["Colonia"]}')
        st.write(f'Código postal: {user_data["Código postal"]}')
        st.write(f'Correo: {user_data["Correo"]}')
        st.write(f'Celular: {user_data["Celular"]}')
        st.write(f'Teléfono: {user_data["Teléfono"]}')

if selected == 'Exámenes de laboratorio':
        def mostrar_archivos_pdf():
          st.subheader("Archivos")
          st.info('Selecciona el archivo a descargar:')
          pdf_files = [f for f in os.listdir("pdf_files") if f.endswith('.pdf')]
          if pdf_files:
              for pdf in pdf_files:
                  file_path = os.path.join("pdf_files", pdf)
                  with open(file_path, "rb") as f:
                      base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                  download_link = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{pdf}">Descargar {pdf}</a>'
                  st.markdown(download_link, unsafe_allow_html=True)
          else:
              st.error("No hay archivos PDF disponibles para descargar.")

        mostrar_archivos_pdf()

def load_med(patient_id):
    file_path = f'{patient_id}_medicamentos.csv'
    try:
        med_df = pd.read_csv(file_path)
        if 'Tratamiento_Terminado' not in med_df.columns:
            med_df['Tratamiento_Terminado'] = False
    except FileNotFoundError:
        med_df = pd.DataFrame(columns=['Medicamento', 'Concentracion', 'Fecha', 'Doctor_ID', 'Fecha_Inicio', 'Fecha_Fin', 'Tratamiento_Terminado'])
    return med_df

def update_treatment_status(patient_id, med_df):
    file_path = f'{patient_id}_medicamentos.csv'
    med_df.to_csv(file_path, index=False)
    st.success("El estado del tratamiento ha sido actualizado.")

if user_type == 'paciente':
    if selected == 'Medicamentos':
        st.title('Medicamentos')

        patient_id = user_data['ID']

        med_df = load_med(patient_id)

        if not med_df.empty:
            st.subheader('Medicamentos del paciente:')

            gb = GridOptionsBuilder.from_dataframe(med_df)
            gb.configure_column("Tratamiento_Terminado", editable=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                med_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                fit_columns_on_grid_load=True
            )

            updated_med_df = grid_response['data']

            if not med_df.equals(updated_med_df):
                update_treatment_status(patient_id, updated_med_df)

        else:
            st.write("No se han registrado medicamentos para este paciente.")

if selected == 'Ruta quirúrgica':
  usuarios_pacientes = pd.read_excel("usuarios.xlsx")
  selected = st.session_state.get('selected', None)
  patient_data = st.session_state.get('user_data', None)

  if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:
          nombre = patient_info['Nombre(s)'].iloc[0]
          ap_paterno = patient_info['Apellido paterno'].iloc[0]
          ap_materno = patient_info['Apellido materno'].iloc[0]
          patient_id = patient_info['ID'].iloc[0]

          st.title(f'Ruta quirúrgica de, {nombre} {ap_paterno} {ap_materno} {patient_id}')
          st.write(f"""

              En esta sección, puedes encontrar detalles sobre tu ruta quirúrgica. La tabla a continuación muestra información importante sobre tus cirugías planificadas, incluyendo el nombre de la cirugía, el nombre del doctor encargado, la fecha programada, y el estado actual de la cirugía (pendiente, en proceso, realizada).

              Si tienes alguna pregunta o inquietud, no dudes en comunicarte con tu médico.

              ¡Gracias por confiar en nosotros con tu cuidado médico!
              """)

          file_path = f"editable_dataframe_{patient_id}.csv"

          if os.path.exists(file_path):
              saved_df = pd.read_csv(file_path)
              st.write(saved_df)
          else:
              st.error("No se encontró ningún historial guardado para este paciente.")


def save_diag(diagnostico, patient_id, doctor_id, fecha):
        diag_df = load_diag(patient_id)
        new_diag = pd.DataFrame({
            'Diagnostico': [diagnostico],
            'patient_id': [patient_id],
            'Fecha': [fecha],
            'Doctor_ID': [doctor_id],
            'Tratamiento_Terminado': [False]
        })
        diag_df = pd.concat([diag_df, new_diag], ignore_index=True)
        file_path = f'{patient_id}_diagnosticos.csv'
        diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha guardado el diagnóstico del paciente {patient_id} en '{file_path}'")

def load_diag(patient_id):
        file_path = f'{patient_id}_diagnosticos.csv'
        try:
            diag_df = pd.read_csv(file_path)
            if 'Tratamiento_Terminado' not in diag_df.columns:
                diag_df['Tratamiento_Terminado'] = False
        except FileNotFoundError:
            diag_df = pd.DataFrame(columns=['Diagnostico', 'Fecha', 'patient_id', 'Doctor_ID', 'Tratamiento_Terminado'])
        return diag_df

def update_treatment_status(patient_id, updated_diag_df):
        file_path = f'{patient_id}_diagnosticos.csv'
        updated_diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha actualizado el estado del tratamiento del paciente {patient_id}")

if selected == 'Diagnósticos médicos':
      st.title('Mis Diagnósticos')
      st.write(f"""
      En esta sección, puedes encontrar detalles sobre tus diagnósticos médicos. La tabla a continuación muestra información importante sobre tus diagnósticos recientes, incluyendo el nombre del diagnóstico, el nombre del doctor que lo realizó, la fecha del diagnóstico, y el estado actual (activo, en remisión, resuelto).

      Si tienes alguna pregunta o inquietud, no dudes en comunicarte con tu médico.

      ¡Gracias por confiar en nosotros con tu cuidado médico!
      """)

      patient_id = user_data['ID']

      diag_df = load_diag(patient_id)
      if not diag_df.empty:
            st.subheader('Diagnósticos actuales:')
            st.write(diag_df)
      else:
            st.error("No se han registrado diagnósticos para este paciente.")


if selected == 'Imágenes médicas':
      st.title('Imágenes médicas')
      st.write("Dado el tiempo limitado disponible para el proyecto y la falta de experiencia en TI en la aplicación de NEXIA, no se implementará un programa para la lectura de imágenes médicas en esta fase.\n\nSin embargo, es importante considerar la implementación de esta funcionalidad en el futuro para que la aplicación pueda ser una herramienta completa y eficaz en su campo.\n\nA continuación, se presentarán algunas imágenes que ilustran cómo debería verse esta funcionalidad cuando se integre en la aplicación con los avances tecnológicos actuales.")

      VIDEO_URL = "https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME"
      st.video(VIDEO_URL)

      st.write('Creador: TIME')
      st.write('How AI Could Change the Future of Medicine')
      st.write('URL: https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME')

      with st.expander('Noticias'):
          st.write('A continuación, se presentarán diversas noticias sobre la implementación de sistemas de imágenes médicas en aplicaciones similares a NEXIA, demostrando que es una posibilidad viable.')
          st.write(" - Caja pone en marcha proyecto Redimed para digitalizar servicios de radiología [Link](https://www.ccss.sa.cr/noticia?v=caja-pone-en-marcha-proyecto-redimed-para-digitalizar-servicios-de-radiologia)")
          st.write(' - CCSS registrará las radiografías para que estén a disposición de todos los médicos [Link](https://amprensa.com/2022/11/ccss-registrara-las-radiografias-para-que-esten-a-disposicion-de-todos-los-medicos/)')
          st.write(' - Mejores aplicaciones DICOM para móvil (Android and iOS)[Link](https://www.imaios.com/es/recursos/blog/mejor-aplicacion-dicom-movil)')

def obtener_informacion_vacunas(patient_id):
    pacientes = pd.read_excel('usuarios.xlsx')
    dosis = pd.read_excel('dosis.xlsx')
    vacunas = pd.read_excel('vacunas.xlsx')

    dosis_paciente = dosis[dosis['ID'] == patient_id]

    vacunas_paciente = vacunas[vacunas['ID_vacuna'].isin(dosis_paciente['ID_vacuna'])]

    informacion_paciente = pd.merge(vacunas_paciente, dosis_paciente, on='ID_vacuna')

    informacion_paciente = informacion_paciente[['Nombre', 'Descripción', 'Lote', 'Fecha de aplicación']]

    return informacion_paciente

if selected == 'Vacunas':
    st.title('Vacunas')
    st.write(f"""

              En esta sección, puedes encontrar detalles sobre tu historial de vacunación. A continuación se muestra información sobre las vacunas que has recibido, incluyendo el nombre de la vacuna, una breve descripción, el número de lote y la fecha de aplicación.

              Es importante mantener un registro actualizado de tus vacunas para garantizar una buena salud y prevenir enfermedades. Si tienes alguna pregunta sobre tus vacunas o necesitas más información, no dudes en comunicarte con tu médico.

              ¡Gracias por mantener tu historial de vacunación al día y cuidar de tu salud!
              """)

    st.write('Información de vacunas del paciente:')

    patient_id = st.session_state.get('user_data', {}).get('ID', None)

    if patient_id is not None:
        informacion_paciente = obtener_informacion_vacunas(patient_id)

        st.info("Por favor, seleccione una vacuna para ver la información.")

        for index, vacuna in informacion_paciente.iterrows():
            with st.expander(f"Vacuna: {vacuna['Nombre']}"):
                st.write(f"Nombre: {vacuna['Nombre']}")
                st.write(f"Descripción: {vacuna['Descripción']}")
                st.write(f"Lote: {vacuna['Lote']}")
                st.write(f"Fecha de aplicación: {vacuna['Fecha de aplicación']}")

    else:
        st.write("No se ha encontrado información del paciente.")

def display_allergies_table(patient_id):
    allergies_data = load_allergies(patient_id)
    if not allergies_data.empty:
        st.subheader("Alergias del paciente")
        st.write(allergies_data)
    else:
        st.write("No hay datos de alergias para mostrar.")

def save_allergies(selected_allergies, patient_id):
    allergies_df = pd.DataFrame({"Alergias": list(selected_allergies)})
    file_path = f"{patient_id}_alergias.csv"
    allergies_df.to_csv(file_path, index=False)
    st.success(f"Se han guardado las alergias del paciente {patient_id} en '{file_path}'")

def load_allergies(patient_id):
    try:
        allergies_df = pd.read_csv(f"{patient_id}_alergias.csv")
    except FileNotFoundError:
        allergies_df = pd.DataFrame(columns=["Alergias"])
    return allergies_df

if selected == 'Alergias':
  st.title('Alergias')
  st.write('Selecciona las alergias que padeces:')
  alergias = pd.read_excel("Alergias.xlsx")
  usuarios_pacientes = pd.read_excel("usuarios.xlsx")
  selected = st.session_state.get('selected',None)
  patient_data = st.session_state.get('user_data',None)
  if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:

        st.session_state.patient_id = patient_info['ID'].iloc[0]

  opciones_alergias = alergias['Alergia alimentaria'].dropna().unique()
  opciones_alergias1 = alergias['Alergia estacional'].dropna().unique()
  opciones_alergias2 = alergias['Alergias de interiores'].dropna().unique()
  opciones_alergias3 = alergias['Asma alérgica'].dropna().unique()

  if 'selected_allergies' not in st.session_state:
      st.session_state.selected_allergies = set()

  with st.expander("Alergias alimentarias"):
      st.write('Descripción: Una alergia alimentaria se produce cuando el sistema inmunitario del cuerpo reacciona de forma anómala a algo que suele ser inofensivo para la mayoría de las personas, como las proteínas de la leche o los huevos.')

      for opcion in opciones_alergias:
          checkbox_key = f"Alergias alimentarias-{opcion}"
          option_enabled = st.checkbox(opcion, key=checkbox_key, value=opcion in st.session_state.selected_allergies)
          if option_enabled and opcion not in st.session_state.selected_allergies:
              st.session_state.selected_allergies.add(opcion)
          elif not option_enabled and opcion in st.session_state.selected_allergies:
              st.session_state.selected_allergies.remove(opcion)

  with st.expander("Alergias estacionales"):
      st.write('Descripción: Se denomina alergia estacional, o también rinitis alérgica o fiebre del heno, a aquella que ocurre durante una época específica del año.')

      for opcion1 in opciones_alergias1:
          checkbox_key = f"Alergias estacionales-{opcion1}"
          option_enabled = st.checkbox(opcion1, key=checkbox_key, value=opcion1 in st.session_state.selected_allergies)
          if option_enabled and opcion1 not in st.session_state.selected_allergies:
              st.session_state.selected_allergies.add(opcion1)
          elif not option_enabled and opcion1 in st.session_state.selected_allergies:
              st.session_state.selected_allergies.remove(opcion1)

  with st.expander("Alergias de interiores"):
      st.write('Descripción: La alergia en interiores suele ser causa de síntomas durante todo el año, por lo que a veces se denomina alergia crónica o perenne.')

      for opcion2 in opciones_alergias2:
          checkbox_key = f"Alergias de interiores-{opcion2}"
          option_enabled = st.checkbox(opcion2, key=checkbox_key, value=opcion2 in st.session_state.selected_allergies)
          if option_enabled and opcion2 not in st.session_state.selected_allergies:
              st.session_state.selected_allergies.add(opcion2)
          elif not option_enabled and opcion2 in st.session_state.selected_allergies:
              st.session_state.selected_allergies.remove(opcion2)

  with st.expander("Asma alérgica"):
      st.write('Descripción: El asma alérgica, o asma inducida por alergia, es un tipo de asma que la alergia desencadena o empeora. La exposición a alérgenos (por ejemplo, polen, caspa, moho, etc.) o a irritantes a los que los pacientes están sensibilizados puede aumentar los síntomas y precipitar las exacerbaciones en los pacientes con asma.')

      for opcion3 in opciones_alergias3:
          checkbox_key = f"Asma alérgica-{opcion3}"
          option_enabled = st.checkbox(opcion3, key=checkbox_key, value=opcion3 in st.session_state.selected_allergies)
          if option_enabled and opcion3 not in st.session_state.selected_allergies:
              st.session_state.selected_allergies.add(opcion3)
          elif not option_enabled and opcion3 in st.session_state.selected_allergies:
              st.session_state.selected_allergies.remove(opcion3)

  nueva_alergia_personalizada = st.text_input("Si tu alergia no está en la lista, por favor añádela aquí:",placeholder='Ingresa la alergia aquí')

  if nueva_alergia_personalizada and nueva_alergia_personalizada not in st.session_state.selected_allergies:
      st.session_state.selected_allergies.add(nueva_alergia_personalizada)

  if 'patient_id' not in st.session_state:
      st.session_state.patient_id = None

  if st.button("Guardar alergias"):
      save_allergies(st.session_state.selected_allergies, st.session_state.patient_id)

  st.subheader("¡Alergias guardadas!")
  allergies_data = load_allergies(st.session_state.patient_id)
  st.write(allergies_data)

def load_symptoms_data(patient_id):
    try:
        symptoms_data = pd.read_csv(f"{patient_id}_symptoms_data.csv", usecols=["Fecha", "Síntomas"])
    except FileNotFoundError:
        symptoms_data = pd.DataFrame(columns=["Fecha", "Síntomas"])
    return symptoms_data

def add_symptoms(patient_id, date, symptom, symptoms_data):
    new_row = {"Fecha": date, "Síntomas": ", ".join(symptom)}
    new_df = pd.DataFrame([new_row], columns=["Fecha", "Síntomas"])  # Especificar las columnas deseadas
    symptoms_data = pd.concat([symptoms_data, new_df], ignore_index=True)
    symptoms_data.to_csv(f"{patient_id}_symptoms_data.csv", index=False)
    return symptoms_data

if selected == 'Registro de síntomas':
    usuarios_pacientes = pd.read_excel("usuarios.xlsx")
    selected = st.session_state.get('selected',None)
    patient_data = st.session_state.get('user_data',None)
    if patient_data is not None:
      patient_info = usuarios_pacientes.loc[usuarios_pacientes['ID'] == patient_data['ID']]
      if not patient_info.empty:

        id = patient_info['ID'].iloc[0]


    symptoms_list = ["Fiebre", "Tos", "Dolor de garganta", "Congestión nasal", "Dificultad para respirar", "Fatiga", "Dolor de cabeza", "Náuseas", "Dolor muscular", "Pérdida del gusto u olfato"]

    symptoms_data = load_symptoms_data(id)

    st.title("Registro de Síntomas Diarios")
    st.write("Por favor, seleccione sus síntomas diarios:")

    with st.form(key='symptoms_form'):
        date = st.date_input("Fecha", value=pd.Timestamp.today())
        selected_symptoms = st.multiselect("Síntomas", symptoms_list)
        submit_button = st.form_submit_button(label='Guardar')

    if submit_button:
        symptoms_data = add_symptoms(id,date, selected_symptoms, symptoms_data)
        st.success("¡Síntomas guardados exitosamente para el día {}!".format(date))

    st.subheader("Registro de Síntomas Actual")
    st.write(symptoms_data)

if selected == 'Doctor':
    usuarios_doc = pd.read_excel("usuarios_doc.xlsx")
    selected = st.session_state.get('selected', None)
    st.title("Información de Doctor")
    doctor_data = st.session_state.get('user_data', None)
    if doctor_data is not None:
        doctor_info = usuarios_doc.loc[usuarios_doc['ID'] == doctor_data['ID']]
        if not doctor_info.empty:
            nombre = doctor_info['Nombre(s)'].iloc[0]
            ap_paterno = doctor_info['Apellido paterno'].iloc[0]
            ap_materno = doctor_info['Apellido materno'].iloc[0]
            doc_rol = doctor_info['Rol del usuario'].iloc[0]
            especialidad = doctor_info['Especialidad'].iloc[0]
            subespecialidad = doctor_info['Sub-especialidad'].iloc[0]
            clues = doctor_info['Clave única de establecimiento de salud'].iloc[0]
            celular = doctor_info['Celular'].iloc[0]
            id = doctor_info['ID'].iloc[0]

            st.subheader(f'Bienvenido, Dr. {nombre} {ap_paterno} {ap_materno}')
            col1,col2,col3 = st.columns(3)

            with col2.container():
                col2.metric('Rol de usuario', doc_rol)
                col2.metric("Especialidad", especialidad)
                col2.metric("Sub-especialidad", subespecialidad)

            with col3.container():
                col3.metric('ID', id)
                col3.metric("CLUES", clues)
                col3.metric("Celular", celular)

            try:
                path = f'{id}.jpeg'
                print("Ruta de la imagen:", path)
                image = Image.open(path)
                col1.image(image, caption=f'Dr. {nombre}')
            except FileNotFoundError:
                col1.write('No hay imagen registrada.')

    with st.expander('Buscar doctor...'):
      def display_doctor_info(doctor_info, image_path):
          nombre = doctor_info['Nombre(s)']
          ap_paterno = doctor_info['Apellido paterno']
          ap_materno = doctor_info['Apellido materno']
          doc_rol = doctor_info['Rol del usuario']
          especialidad = doctor_info['Especialidad']
          subespecialidad = doctor_info['Sub-especialidad']
          clues = doctor_info['Clave única de establecimiento de salud']
          celular = doctor_info['Celular']
          id = doctor_info['ID']

          st.subheader(f'Bienvenido, Dr. {nombre} {ap_paterno} {ap_materno}')
          col1, col2, col3 = st.columns(3)

          with col2.container():
              col2.metric('Rol de usuario', doc_rol)
              col2.metric("Especialidad", especialidad)
              col2.metric("Sub-especialidad", subespecialidad)

          with col3.container():
              col3.metric('ID', id)
              col3.metric("CLUES", clues)
              col3.metric("Celular", celular)

          try:
              image = Image.open(image_path)
              col1.image(image, caption=f'Dr. {nombre}')
          except FileNotFoundError:
              col1.write('No hay imagen registrada.')

      st.subheader("Buscar Doctores por Especialidad y Sub-especialidad")

      especialidades = usuarios_doc['Especialidad'].unique()
      subespecialidades = usuarios_doc['Sub-especialidad'].unique()

      especialidad_select = st.selectbox("Seleccione una especialidad:", especialidades)
      subespecialidad_select = st.selectbox("Seleccione una sub-especialidad (opcional):", [''] + list(subespecialidades))

      if subespecialidad_select != '':
          filtered_doctors = usuarios_doc[(usuarios_doc['Especialidad'] == especialidad_select) &
                                          (usuarios_doc['Sub-especialidad'] == subespecialidad_select)]
      else:
          filtered_doctors = usuarios_doc[usuarios_doc['Especialidad'] == especialidad_select]

      if not filtered_doctors.empty:
          for index, doctor_info in filtered_doctors.iterrows():
              doctor_id = doctor_info['ID']
              image_path = f'{doctor_id}.jpeg'
              display_doctor_info(doctor_info, image_path)
      else:
          st.error("No se encontraron doctores con la especialidad y sub-especialidad seleccionadas.")

def display_patient_data_by_id(patient_id):
    symptoms_data = load_symptoms_data(patient_id)  
    if not symptoms_data.empty:
        st.subheader("Registro de Síntomas Actual")
        st.write(symptoms_data[["Fecha", "Síntomas"]])
    else:
        st.write("No hay datos de síntomas para mostrar.")

if selected == 'Pacientes':
    pacientes = pd.read_excel('usuarios.xlsx')
    st.title("Información de Paciente")

    search_by_id = st.sidebar.checkbox('Buscar por ID')
    search_by_info = st.sidebar.checkbox('Buscar por información')

    if search_by_id:
        ingresado_id = st.sidebar.text_input('Ingresar ID del paciente:', '')
        matches1 = pacientes[pacientes['ID'] == ingresado_id]

        if not matches1.empty:
            paciente_seleccionado1 = matches1.iloc[0]
            id_paciente_seleccionado = paciente_seleccionado1['ID']
            st.session_state['user_data'] = {'ID': id_paciente_seleccionado}

            paciente_seleccionado1 = matches1.iloc[0]
            name = paciente_seleccionado1['Nombre(s)']
            ap_materno = paciente_seleccionado1['Apellido materno']
            ap_paterno = paciente_seleccionado1['Apellido paterno']
            altura = str(paciente_seleccionado1['Altura'])
            peso = str(paciente_seleccionado1['Peso'])
            nacimiento = str(paciente_seleccionado1['Día de nacimiento']) + '/' + \
                str(paciente_seleccionado1['Mes de nacimiento']) + '/' + \
                str(paciente_seleccionado1['Año de nacimiento'])
            ocupacion = paciente_seleccionado1['Ocupación']
            edad = paciente_seleccionado1['Edad']
            padecimiento = paciente_seleccionado1['Padecimientos']
            sangre = paciente_seleccionado1['Tipo de sangre']
            alergias = paciente_seleccionado1['Alergias']
            medicacion = paciente_seleccionado1['Medicación actual']
            organos = paciente_seleccionado1['Donante de organos']
            genero = paciente_seleccionado1['Género']
            estado_civil = paciente_seleccionado1['Estado civil']
            grupo = paciente_seleccionado1['Grupo étnico']
            religion = paciente_seleccionado1['Religión']
            vivienda = paciente_seleccionado1['Vivienda']
            calle = paciente_seleccionado1['Calle']
            num_ext = paciente_seleccionado1['Número ext']
            num_int = paciente_seleccionado1['Número int']
            Estado = paciente_seleccionado1['Estado']
            municipio = paciente_seleccionado1['Municipio']
            colonia = paciente_seleccionado1['Colonia']
            cod_postal = paciente_seleccionado1['Código postal']
            correo = paciente_seleccionado1['Correo']
            celular = paciente_seleccionado1['Celular']
            tel = paciente_seleccionado1['Teléfono']
            contact_emerg = paciente_seleccionado1['Contacto de emergencia']
            id = paciente_seleccionado1['ID']

            st.subheader(f"{name} {ap_paterno} {ap_materno} {id}")

            col1, col2, col3, col4 = st.columns(4)

            with col2.container():
                col2.metric('Fecha de Nacimiento', nacimiento)
                col2.metric("Ocupación", ocupacion)
                col2.metric("Estado Civil", estado_civil)
                col2.metric("Género", genero)

            with col3.container():
                col3.metric("Altura", altura)
                col3.metric("Peso", peso)
                col3.metric("Edad", edad)
                col3.metric("Tipo de sangre", sangre)

            with col4.container():
                col4.metric("Donante de órganos", organos)
                col4.metric('Padecimiento', padecimiento)
                col4.metric("Alergias", alergias)
                col4.metric('Medicación actual', medicacion)

            try:
              path = f'{id}.jpeg'
              print("Ruta de la imagen:", path)
              image = Image.open(path)
              col1.image(image, caption=f'Paciente {name} {ap_paterno} {ap_materno}')

            except FileNotFoundError:
                col1.write('No hay imagen registrada.')

            with st.expander("Datos generales"):
                st.write(f'Grupo étnico: {grupo}')
                st.write(f'Religión: {religion}')
                st.write(f'Vivienda: {vivienda}')

            with st.expander("Domicilio"):
                st.write(f'Calle: {calle}')
                st.write(f'Número ext: {num_ext}')
                st.write(f'Número int: {num_int}')
                st.write(f'Estado: {Estado}')
                st.write(f'Municipio: {municipio}')
                st.write(f'Colonia: {colonia}')
                st.write(f'Código postal: {cod_postal}')

            with st.expander('Contacto'):
                st.write(f'Correo: {correo}')
                st.write(f'Celular: {celular}')
                st.write(f'Teléfono: {tel}')
                st.write(f'Contacto de emergencia: {contact_emerg}')
        else:
            st.write("No se encontraron coincidencias.")

    elif search_by_info:
        st.sidebar.write('Ingresa los datos para buscar:')
        ingresado_nombre = st.sidebar.text_input('Nombre del Paciente:', '').lower()
        ingresado_apellido_materno = st.sidebar.text_input('Apellido materno:', '').lower()
        ingresado_apellido_paterno = st.sidebar.text_input('Apellido paterno:', '').lower()
        ingresado_dia_nacimiento = st.sidebar.text_input('Día de nacimiento:', '').lower()
        ingresado_mes_nacimiento = st.sidebar.text_input('Mes de nacimiento:', '').lower()
        ingresado_año_nacimiento = st.sidebar.text_input('Año de nacimiento:', '').lower()

        matches = pacientes[
            (pacientes['Nombre(s)'].str.lower() == ingresado_nombre) &
            (pacientes['Apellido materno'].str.lower() == ingresado_apellido_materno) &
            (pacientes['Apellido paterno'].str.lower() == ingresado_apellido_paterno) &
            (pacientes['Día de nacimiento'].astype(str) == ingresado_dia_nacimiento) &
            (pacientes['Mes de nacimiento'].astype(str) == ingresado_mes_nacimiento) &
            (pacientes['Año de nacimiento'].astype(str) == ingresado_año_nacimiento)
        ]

        if not matches.empty:
            paciente_seleccionado1 = matches.iloc[0]
            id_paciente_seleccionado = paciente_seleccionado1['ID']
            st.session_state['user_data'] = {'ID': id_paciente_seleccionado}

            paciente_seleccionado = matches.iloc[0]
            name = paciente_seleccionado['Nombre(s)']
            ap_materno = paciente_seleccionado['Apellido materno']
            ap_paterno = paciente_seleccionado['Apellido paterno']
            altura = str(paciente_seleccionado['Altura'])
            peso = str(paciente_seleccionado['Peso'])
            nacimiento = str(paciente_seleccionado['Día de nacimiento']) + '/' + \
                str(paciente_seleccionado['Mes de nacimiento']) + '/' + \
                str(paciente_seleccionado['Año de nacimiento'])
            ocupacion = paciente_seleccionado['Ocupación']
            edad = paciente_seleccionado['Edad']
            padecimiento = paciente_seleccionado['Padecimientos']
            sangre = paciente_seleccionado['Tipo de sangre']
            alergias = paciente_seleccionado['Alergias']
            medicacion = paciente_seleccionado['Medicación actual']
            organos = paciente_seleccionado['Donante de organos']
            genero = paciente_seleccionado['Género']
            estado_civil = paciente_seleccionado['Estado civil']
            grupo = paciente_seleccionado['Grupo étnico']
            religion = paciente_seleccionado['Religión']
            vivienda = paciente_seleccionado['Vivienda']
            calle = paciente_seleccionado['Calle']
            num_ext = paciente_seleccionado['Número ext']
            num_int = paciente_seleccionado['Número int']
            Estado = paciente_seleccionado['Estado']
            municipio = paciente_seleccionado['Municipio']
            colonia = paciente_seleccionado['Colonia']
            cod_postal = paciente_seleccionado['Código postal']
            correo = paciente_seleccionado['Correo']
            celular = paciente_seleccionado['Celular']
            tel = paciente_seleccionado['Teléfono']
            contact_emerg = paciente_seleccionado['Contacto de emergencia']
            id = paciente_seleccionado['ID']

            st.subheader(f"{name} {ap_paterno} {ap_materno} {id}")

            col1, col2, col3 = st.columns(3)

            with col1.container():
                col1.metric('Fecha de Nacimiento', nacimiento)
                col1.metric("Ocupación", ocupacion)
                col1.metric("Estado Civil", estado_civil)
                col1.metric("Género", genero)

            with col2.container():
                col2.metric("Altura", altura)
                col2.metric("Peso", peso)
                col2.metric("Edad", edad)
                col2.metric("Tipo de sangre", sangre)

            with col3.container():
                col3.metric("Donante de órganos", organos)
                col3.metric('Padecimiento', padecimiento)
                col3.metric("Alergias", alergias)
                col3.metric('Medicación actual', medicacion)

            with st.expander("Datos generales"):
                st.write(f'Grupo étnico: {grupo}')
                st.write(f'Religión: {religion}')
                st.write(f'Vivienda: {vivienda}')

            with st.expander("Domicilio"):
                st.write(f'Calle: {calle}')
                st.write(f'Número ext: {num_ext}')
                st.write(f'Número int: {num_int}')
                st.write(f'Estado: {Estado}')
                st.write(f'Municipio: {municipio}')
                st.write(f'Colonia: {colonia}')
                st.write(f'Código postal: {cod_postal}')

            with st.expander('Contacto'):
                st.write(f'Correo: {correo}')
                st.write(f'Celular: {celular}')
                st.write(f'Teléfono: {tel}')
                st.write(f'Contacto de emergencia: {contact_emerg}')
        else:
            st.write("No se encontraron coincidencias.")
    else:
        st.sidebar.write('Selecciona al menos una opción para buscar.')

    selected = option_menu(
          menu_title= None,
          options = ['Citas','Medicamentos', 'Exámenes de laboratorio','Vacunas','Alergias','Ruta quirúrgica','Imágenes médicas','Diagnósticos médicos','Regístro de síntomas'],
          icons = ['book','capsule-pill', 'droplet','clipboard2-pulse-fill','flower1','heart-pulse','card-image','hospital','activity'],
          orientation = 'horizontal',
          menu_icon = None,
          styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": '#84D9C1'},
          }
    )

    if selected == 'Imágenes médicas':
      st.title('Imágenes médicas')
      st.write("Dado el tiempo limitado disponible para el proyecto y la falta de experiencia en TI en la aplicación de NEXIA, no se implementará un programa para la lectura de imágenes médicas en esta fase.\n\nSin embargo, es importante considerar la implementación de esta funcionalidad en el futuro para que la aplicación pueda ser una herramienta completa y eficaz en su campo.\n\nA continuación, se presentarán algunas imágenes que ilustran cómo debería verse esta funcionalidad cuando se integre en la aplicación con los avances tecnológicos actuales.")

      VIDEO_URL = "https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME"
      st.video(VIDEO_URL)

      st.write('Creador: TIME')
      st.write('How AI Could Change the Future of Medicine')
      st.write('URL: https://www.youtube.com/watch?v=YSQRWOy2Om4&ab_channel=TIME')

      with st.expander('Noticias'):
          st.write('A continuación, se presentarán diversas noticias sobre la implementación de sistemas de imágenes médicas en aplicaciones similares a NEXIA, demostrando que es una posibilidad viable.')
          st.write(" - Caja pone en marcha proyecto Redimed para digitalizar servicios de radiología [Link](https://www.ccss.sa.cr/noticia?v=caja-pone-en-marcha-proyecto-redimed-para-digitalizar-servicios-de-radiologia)")
          st.write(' - CCSS registrará las radiografías para que estén a disposición de todos los médicos [Link](https://amprensa.com/2022/11/ccss-registrara-las-radiografias-para-que-esten-a-disposicion-de-todos-los-medicos/)')
          st.write(' - Mejores aplicaciones DICOM para móvil (Android and iOS)[Link](https://www.imaios.com/es/recursos/blog/mejor-aplicacion-dicom-movil)')

    if selected == 'Regístro de síntomas':
          display_patient_data_by_id(id)

    def display_patient_allergies(patient_id):
        allergies_data = load_allergies(patient_id)
        if not allergies_data.empty:
            st.subheader("Alergias del paciente")
            st.write(allergies_data)
        else:
            st.write("No hay datos de alergias para mostrar.")
    if selected == 'Alergias':
      patient_id = st.selectbox("Seleccione al paciente:", pacientes['ID'])
      display_patient_allergies(patient_id)

    if selected == 'Vacunas':
          st.title('Vacunas')
          st.write('Información de vacunas del paciente:')

          patient_id = st.session_state.get('user_data', {}).get('ID', None)

          if patient_id is not None:
                  informacion_paciente = obtener_informacion_vacunas(patient_id)

                  st.info("Por favor, seleccione una vacuna para ver la información.")

                  for index, vacuna in informacion_paciente.iterrows():
                    with st.expander(f"Vacuna: {vacuna['Nombre']}"):
                          st.write(f"Nombre: {vacuna['Nombre']}")
                          st.write(f"Descripción: {vacuna['Descripción']}")
                          st.write(f"Lote: {vacuna['Lote']}")
                          st.write(f"Fecha de aplicación: {vacuna['Fecha de aplicación']}")

          else:
                  st.write("No se ha seleccionado ningún paciente.")

    def save_diag(diagnostico, patient_id, doctor_id, fecha):
        diag_df = load_diag(patient_id)
        new_diag = pd.DataFrame({
            'Diagnostico': [diagnostico],
            'patient_id': [patient_id],
            'Fecha': [fecha],
            'Doctor_ID': [doctor_id],
            'Tratamiento_Terminado': [False]
        })
        diag_df = pd.concat([diag_df, new_diag], ignore_index=True)
        file_path = f'{patient_id}_diagnosticos.csv'
        diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha guardado el diagnóstico del paciente {patient_id} en '{file_path}'")

    def load_diag(patient_id):
        file_path = f'{patient_id}_diagnosticos.csv'
        try:
            diag_df = pd.read_csv(file_path)
            if 'Tratamiento_Terminado' not in diag_df.columns:
                diag_df['Tratamiento_Terminado'] = False
        except FileNotFoundError:
            diag_df = pd.DataFrame(columns=['Diagnostico', 'Fecha', 'patient_id', 'Doctor_ID', 'Tratamiento_Terminado'])
        return diag_df

    def update_treatment_status(patient_id, updated_diag_df):
        file_path = f'{patient_id}_diagnosticos.csv'
        updated_diag_df.to_csv(file_path, index=False)
        st.success(f"Se ha actualizado el estado del tratamiento del paciente {patient_id}")

    if selected == 'Diagnósticos médicos':
        st.title('Diagnósticos del paciente')

        patient_id = st.text_input('Ingresar el ID del paciente', key='patient_id_input')

        if patient_id:
            diag = pd.read_excel('CIE-10_DIAGNOSTICOS_ACTABR2024.xlsx')
            selected_diag = st.selectbox('Seleccione el diagnóstico:', diag['NOMBRE'].unique(), key='diagnostico_select')
            doctor_id = st.text_input('Ingrese el ID del Doctor:', key='doctor_id_input')
            fecha = datetime.now().strftime("%Y-%m-%d")

            if st.button('Generar diagnóstico', key='generate_diagnosis_button'):
                if selected_diag and patient_id and doctor_id:
                    save_diag(selected_diag, patient_id, doctor_id, fecha)
                else:
                    st.error('Por favor, complete todos los campos.')

            diag_df = load_diag(patient_id)
            if not diag_df.empty:
                st.subheader('Diagnósticos actuales del paciente.')

                gb = GridOptionsBuilder.from_dataframe(diag_df)
                gb.configure_column("Tratamiento_Terminado", editable=True)
                grid_options = gb.build()

                grid_response = AgGrid(
                    diag_df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=True
                )

                updated_diag_df = grid_response['data']

                if not diag_df.equals(updated_diag_df):
                    update_treatment_status(patient_id, updated_diag_df)
            else:
                st.error('No se han registrado diagnósticos para este paciente.')


    def save_medic(medicamento, concentracion, patient_id, doctor_id, start_date, end_date):
        med_df = load_med(patient_id)
        new_med = pd.DataFrame({
            'Medicamento': [medicamento],
            'Concentracion': [concentracion],
            'Fecha': [datetime.now().strftime("%Y-%m-%d")],
            'Doctor_ID': [doctor_id],
            'Fecha_Inicio': [start_date],
            'Fecha_Fin': [end_date],
            'Tratamiento_Terminado': [False]
        })
        med_df = pd.concat([med_df, new_med], ignore_index=True)
        file_path = f'{patient_id}_medicamentos.csv'
        med_df.to_csv(file_path, index=False)
        st.success(f"Se ha guardado el medicamento del paciente {patient_id} en '{file_path}'")

    def load_med(patient_id):
        file_path = f'{patient_id}_medicamentos.csv'
        try:
            med_df = pd.read_csv(file_path)
            if 'Tratamiento_Terminado' not in med_df.columns:
                med_df['Tratamiento_Terminado'] = False
        except FileNotFoundError:
            med_df = pd.DataFrame(columns=['Medicamento', 'Concentracion', 'Fecha', 'Doctor_ID', 'Fecha_Inicio', 'Fecha_Fin', 'Tratamiento_Terminado'])
        return med_df


    if selected == 'Medicamentos':
            st.title('Recetar Medicamento')

            patient_id = st.text_input('ID del paciente')

            if patient_id:
                med = pd.read_excel('MEDICAMENTOS_ENERO_2022.xlsx')
                selected_med = st.selectbox('Seleccione el medicamento:', med['NOMBRE GENERICO'].unique())
                selected_concentracion = st.selectbox('Seleccione la concentración:', med[med['NOMBRE GENERICO'] == selected_med]['CONCENTRACION'].unique())
                doctor_id = st.text_input('ID del Doctor:')
                start_date = st.date_input('Fecha de inicio del tratamiento')
                end_date = st.date_input('Fecha de finalización del tratamiento')

                if st.button('Generar receta'):
                    if selected_med and patient_id and doctor_id:
                        save_medic(selected_med, selected_concentracion, patient_id, doctor_id, start_date, end_date)
                    else:
                        st.error("Por favor, complete todos los campos.")
                med_df = load_med(patient_id)
                if not med_df.empty:
                  st.subheader('Medicamentos actuales del paciente:')
                  st.write(med_df)
                else:
                  st.error("No se han registrado medicamentos para este paciente.")

    if selected == 'Ruta quirúrgica':

      def create_editable_dataframe(num_rows=5):
          data = {'Cirugía': [''] * num_rows,
                  'Descripción': [''] * num_rows,
                  'ID Doctor': [''] * num_rows,
                  'Especialidad': [''] * num_rows,
                  'Pendiente': [False] * num_rows,
                  'En proceso': [False] * num_rows,
                  'Realizada': [False] * num_rows}

          return pd.DataFrame(data)

      patient_id = st.text_input("Ingrese el ID del paciente:")

      file_path = f"editable_dataframe_{patient_id}.csv"

      if patient_id:
          df = create_editable_dataframe()

          edited_df = st.data_editor(df, num_rows='dynamic')

          if st.button("Guardar cambios"):
              edited_df.to_csv(file_path, index=False)
              st.success("Se guardaron los cambios exitosamente.")
      else:
          st.info("Por favor, ingrese el ID del paciente.")

      if patient_id and st.button("Mostrar historial guardado"):
          if pd.Series([f"{patient_id}.csv" in file for file in os.listdir(".")]).any():
              saved_df = pd.read_csv(file_path)
              st.write(saved_df)
          else:
              st.error("No se encontró información para paciente proporcionado.")

    if selected == 'Exámenes de laboratorio':
      
      def mostrar_archivos_pdf():
        st.subheader("Archivos")
        st.info('Selecciona el archivo a descargar:')
        pdf_files = [f for f in os.listdir("pdf_files") if f.endswith('.pdf')]
        if pdf_files:
            for pdf in pdf_files:
                file_path = os.path.join("pdf_files", pdf)
                with open(file_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                download_link = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{pdf}">Descargar {pdf}</a>'
                st.markdown(download_link, unsafe_allow_html=True)
        else:
            st.error("No hay archivos PDF disponibles para descargar.")

      st.title('Exámenes de laboratorio')
      st.info('Sube el examen a continuación:')
      uploaded_file = st.file_uploader("Subir un archivo PDF", type="pdf")

      if uploaded_file is not None:
          st.success(f"Archivo subido: {uploaded_file.name}")
          
          file_path = os.path.join("pdf_files", uploaded_file.name)
          with open(file_path, "wb") as f:
              f.write(uploaded_file.getbuffer())

      mostrar_archivos_pdf()
