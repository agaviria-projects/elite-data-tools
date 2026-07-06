"""
------------------------------------------------------------
📤 PUSH A GITHUB PAGES – MAPA ANS
------------------------------------------------------------
Autor: Héctor + IA (2025)

Este script:
1. Copia el archivo mapa_ans.html generado por Python
   desde Control_ANS_v5/data_output/
   hacia tu repositorio local:
       C:/Users/Acer/Documents/GitHub/control_ans_v5/

2. Ejecuta automáticamente:
       git add
       git commit
       git push

3. Actualiza la URL pública de GitHub Pages.
------------------------------------------------------------
"""

import shutil
import subprocess
from pathlib import Path

# ============================================================
# 1️⃣ RUTAS IMPORTANTES
# ============================================================

# Ruta donde Python genera el HTML actualizado
ruta_mapa_local = Path(r"C:\Users\Acer\Desktop\Control_ANS_v5\data_output\mapa_ans.html")

# Ruta de tu repositorio local (control_ans_v5)
ruta_repo = Path(r"C:\Users\Acer\Desktop\Control_ANS_v5")

# Archivo destino en el repo
ruta_mapa_repo = ruta_repo / "mapa_ans.html"


# ============================================================
# 2️⃣ COPIAR ARCHIVO AL REPOSITORIO
# ============================================================
print("📁 Copiando archivo HTML actualizado al repositorio local...")

try:
    shutil.copy(ruta_mapa_local, ruta_mapa_repo)
    print("✔ Archivo copiado correctamente.")
except Exception as e:
    print("❌ Error copiando archivo:", e)
    exit()


# ============================================================
# 3️⃣ EJECUTAR COMANDOS GIT
# ============================================================
def ejecutar_git(comando):
    resultado = subprocess.run(
        comando, cwd=ruta_repo, text=True, capture_output=True
    )
    if resultado.returncode == 0:
        print("✔", " ".join(comando))
    else:
        print("❌ Error ejecutando:", " ".join(comando))
        print(resultado.stderr)


print("🔄 Ejecutando comandos Git...")

ejecutar_git(["git", "add", "mapa_ans.html"])
ejecutar_git(["git", "commit", "-m", "Actualización automática del mapa ANS"])
ejecutar_git(["git", "push"])

print("\n🌍 GitHub Pages actualizado correctamente.")
print("URL pública: https://agaviria-projects.github.io/control_ans_v5/mapa_ans.html")
