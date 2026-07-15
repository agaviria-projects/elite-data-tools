import ttkbootstrap as ttk
from tkinter import messagebox

print("=" * 60)
print("SIDEBAR.PY CARGADO")
print(__file__)
print("=" * 60)

from ui.styles import *
from utils.navigation import (
    mostrar_home,
    mostrar_informe_actas,
    mostrar_generador_ans,
    mostrar_validacion_materiales,
    mostrar_compresor_pdf,
    mostrar_whatsapp,
    mostrar_consolidador_excel,
    mostrar_analizador_costos,
    mostrar_calendario_ans,
)
MENU = [
    ('home','🏠','Inicio'),

    ('actas','📊','Informe Actas'),

    ('ans','📈','Generador Informe ANS'),

    ('materiales','🛠️','Validación Materiales'),

    ('pdf','📦','Zip PDF'),

    ('whatsapp','💬','WhatsApp + ANS'),

    ('consolidador','📚','Consolidador Excel'),

    ('costos','💲','Analizador Costos'),

    ('calendario','🗓️','Calendario ANS'),

]

print(MENU)

items_menu={}; barra_menu={}
def activar_menu(act):
    for m,l in items_menu.items():
        l.configure(bootstyle='default',font=('Segoe UI',11))
        barra_menu[m].configure(text=' ')
    items_menu[act].configure(bootstyle='success',font=('Segoe UI',11,'bold'))
    barra_menu[act].configure(text='┃',bootstyle='success')
def abrir_modulo(m,p):
    activar_menu(m)
    if m=='home': mostrar_home(p)
    elif m=='actas': mostrar_informe_actas(p)
    elif m== 'ans': mostrar_generador_ans(p)
    elif m == "materiales": mostrar_validacion_materiales(p)
    elif m=="pdf": mostrar_compresor_pdf(p)
    elif m == "whatsapp": mostrar_whatsapp(p)
    elif m == "consolidador":mostrar_consolidador_excel(p)
    elif m == "costos":mostrar_analizador_costos(p)
    elif m == "calendario":mostrar_calendario_ans(p)
def salir(app):
    if messagebox.askyesno('Salir','¿Desea salir de ELITE Data Tools?'): app.destroy()
def crear_sidebar(app,panel):
    sb=ttk.Frame(app,width=SIDEBAR_WIDTH,padding=18); sb.grid(row=1,column=0,sticky='ns'); sb.grid_propagate(False)
    ttk.Label(sb,text='ELITE',font=('Segoe UI',20,'bold'),bootstyle='success').pack(anchor='w')
    ttk.Label(sb,text='Data Tools Suite',font=FUENTE_PEQUEÑA).pack(anchor='w',pady=(0,15))
    ttk.Separator(sb).pack(fill='x',pady=(0,12))
    ttk.Label(sb,text='MÓDULOS',font=('Segoe UI',9,'bold'), bootstyle='light').pack(anchor='w',pady=(0,10))
    menu=ttk.Frame(sb); menu.pack(fill='x')
    for mod,ico,txt in MENU:
        row=ttk.Frame(menu); row.pack(fill='x',pady=2)
        row.columnconfigure(2,weight=1)
        b=ttk.Label(row,text=' ',width=2,anchor='center',font=('Segoe UI',12,'bold')); b.grid(row=0,column=0)
        barra_menu[mod]=b
        ttk.Label(row,text=ico,font=('Segoe UI Emoji',11)).grid(row=0,column=1,padx=(0,8))
        it=ttk.Label(row,text=txt,font=('Segoe UI',11),cursor='hand2',anchor='w')
        it.grid(row=0,column=2,sticky='ew')
        it.bind('<Button-1>',lambda e,m=mod: abrir_modulo(m,panel)); items_menu[mod]=it
    ttk.Frame(sb).pack(expand=True,fill='both')
    ttk.Separator(sb).pack(fill='x',pady=8)
    ttk.Button(sb, text='🚪 Salir', bootstyle='danger-outline', cursor='hand2', command=lambda: salir(app)).pack(fill='x')
    activar_menu('home'); return sb
