# src/cc_ans_db.py

from pathlib import Path
import sqlite3


def obtener_ruta_db() -> Path:
    """
    Devuelve la ruta absoluta de la base SQLite.
    La base queda en la raíz del proyecto:
    Control_ANS_v5_DEV/atlas360_operacion.db
    """
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "atlas360_operacion.db"


def conectar_db() -> sqlite3.Connection:
    """
    Abre conexión SQLite y activa llaves foráneas.
    """
    db_path = obtener_ruta_db()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def crear_tablas() -> None:
    """
    Crea las tablas base del Centro de Control ANS si no existen.
    """
    conn = conectar_db()
    cur = conn.cursor()

    # 1) Plan base de la mañana
    cur.execute("""
        CREATE TABLE IF NOT EXISTS plan_base_diario (
            fecha_operacion TEXT NOT NULL,
            id_pedido TEXT NOT NULL,
            zona TEXT,
            cuadrilla TEXT,
            ans_limite TEXT,
            estado_inicial TEXT,
            marca_plan TEXT,
            PRIMARY KEY (fecha_operacion, id_pedido)
        );
    """)

    # 2) Registro de cortes cargados
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cortes_operacion (
            id_corte INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_operacion TEXT NOT NULL,
            tipo_corte TEXT,
            marca_corte TEXT,
            archivo_nombre TEXT,
            total_registros INTEGER
        );
    """)

    # 3) Seguimiento del pedido del plan frente a cada corte
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seguimiento_plan (
            id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_corte INTEGER NOT NULL,
            fecha_operacion TEXT NOT NULL,
            id_pedido TEXT NOT NULL,
            zona_actual TEXT,
            estado_actual TEXT,
            marca_temporal TEXT,
            reporte_tecnico TEXT,
            cumple_visita INTEGER DEFAULT 0,
            fuente_visita TEXT,
            nivel_riesgo TEXT,
            FOREIGN KEY (id_corte) REFERENCES cortes_operacion(id_corte)
        );
    """)

    # Índices
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_plan_fecha
        ON plan_base_diario (fecha_operacion);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_plan_pedido
        ON plan_base_diario (id_pedido);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cortes_fecha
        ON cortes_operacion (fecha_operacion);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_seg_fecha
        ON seguimiento_plan (fecha_operacion);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_seg_pedido
        ON seguimiento_plan (id_pedido);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_seg_corte
        ON seguimiento_plan (id_corte);
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    crear_tablas()
    print("✅ Base SQLite inicializada correctamente.")