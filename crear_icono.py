from PIL import Image

# Abrir logo
img = Image.open("assets/logo.png")

# Crear icono (.ico)
img.save(
    "assets/icono.ico",
    format="ICO",
    sizes=[
        (16,16),
        (24,24),
        (32,32),
        (48,48),
        (64,64),
        (128,128),
        (256,256)
    ]
)

print("✅ Icono creado correctamente.")