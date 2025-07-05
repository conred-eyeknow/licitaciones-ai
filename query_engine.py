import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
import openai

# Carga de variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Esquema de tablas que se inyectará en el prompt
TABLE_SCHEMA = """
Tablas disponibles (con descripción de campos relevantes):

pymes(
  id: identificador único de la empresa,
  razon_social: nombre oficial de la empresa
)
licitaciones(
  id: identificador de la licitación,
  fecha_apertura: fecha en que se abrió el concurso
)
juntas(
  id: identificador de la junta,
  licitacion_id: referencia a la licitación,
  tipo: tipo de evento (JA: aclaraciones, VT: visita técnica, PP: propuesta de monto, ADJ: adjudicación, CANC: cancelada)
)
pyme_lctn(
  id: identificador de la participación,
  licitacion_id: referencia a la licitación,
  pyme_id: referencia a la empresa participante,
  junta_id: referencia a la junta correspondiente,
  monto: monto ofertado en ese evento (0 = dato no disponible)
)
"""

# Instrucción para forzar sintaxis MySQL
mysql_instructions = (
    "Usa sintaxis compatible con MySQL/MariaDB: "
    "utiliza LIMIT en lugar de TOP, DATE_SUB/CURDATE() para fechas, "
    "y evita funciones específicas de SQL Server."
)

def get_engine():
    """Construye y retorna el engine de SQLAlchemy para MySQL."""
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db   = os.getenv("DB_NAME")
    url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url)

def generate_sql_and_analysis(question: str):
    """
    Llama a OpenAI para generar un bloque de SQL y un análisis en lenguaje natural.
    Devuelve una tupla (sql, analysis).
    """
    # Construcción del prompt
    prompt = (
        TABLE_SCHEMA + "\n"
        f"Pregunta: \"{question}\"\n\n"
        "Instrucciones:\n"
        "1) Escribe el bloque de SQL que responda la pregunta.\n"
        "2) Bajo un separador ### explica los resultados.\n\n"
        "Formato:\n"
        "```sql\n"
        "-- tu SQL aquí\n"
        "```\n"
        "###\n"
        "Explicación aquí."
    )

    # Llamada a la API de OpenAI
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un experto en SQL y análisis de datos."},
            {"role": "user",   "content": prompt}
        ],
    )

    content = resp.choices[0].message.content

    # Extraer el SQL entre ```sql ... ```
    match = re.search(r"```sql\n(.+?)```", content, flags=re.DOTALL)
    sql = match.group(1).strip() if match else None

    # Extraer el análisis tras el separador ###
    parts = content.split("###")
    analysis = parts[-1].strip() if len(parts) > 1 else ""

    return sql, analysis

def run_query(sql: str):
    """
    Ejecuta el SQL contra MySQL y retorna un pandas DataFrame.
    """
    engine = get_engine()
    df = pd.read_sql(text(sql), engine)
    return df
