# ============================================================
# INTERFAZ.PY - Interfaz grafica de usuario (GUI) para el control de flota
# Requiere: Python 3 + tkinter (incluido en Python estandar)
# ============================================================

import tkinter as tk              # Biblioteca de interfaz grafica
from tkinter import ttk, messagebox  # Widgets mejorados y cuadros de dialogo
import datos                      # Persistencia de datos (lectura/escritura JSON)
import funciones                  # Logica de negocio (vencimientos, etc.)
from gui_helpers import (obtener_alertas, obtener_chofer_activo, info_mata,
                          info_licencia, color_indicador,
                          calcular_gastos, calcular_balance)
from datetime import date         # Fechas para registro de altas/bajas

# Cargar la flota desde el archivo JSON al iniciar la aplicacion
flota = datos.cargar_datos()


# ============================================================
# REFRESCAR SELECCION: Busca un vehiculo por patente en la tabla,
# lo selecciona y actualiza el dashboard. Usado despues de guardar
# cambios (agregar, editar, eliminar, choferes, movimientos).
# ============================================================
def refrescar_seleccion(patente):
    for it in tabla.get_children():
        if tabla.item(it)["values"][0] == patente:
            tabla.selection_set(it)
            actualizar_dashboard_auto(None)
            break


# ============================================================
# ACTUALIZAR DASHBOARD POR PATENTE: Actualiza el panel de control
# directamente con los datos de un vehiculo especifico, sin depender
# de la seleccion de la tabla. Garantiza que los valores se reflejen.
# ============================================================
def actualizar_dashboard_por_patente(p):
    if p not in flota: return
    d = flota[p]
    tg = calcular_gastos(d)
    bal = calcular_balance(d)
    lbl_dash_titulo.config(text="CONTROL: " + p + " (" + d["modelo"] + ")")
    val_ingresos.config(text="${:,.0f}".format(d["ingresos"]))
    val_gastos.config(text="${:,.0f}".format(tg))
    val_balance.config(text="${:,.0f}".format(bal))
    val_balance.config(fg="#F4D03F" if bal >= 0 else "#E74C3C")
    if "vencimiento_matafuego" in d:
        dm = funciones.verificar_vencimiento(d["vencimiento_matafuego"])
        txt, clr = color_indicador(dm, d["vencimiento_matafuego"], umbral=30)
        val_matafuego.config(text=txt, fg=clr)
    ds = funciones.verificar_vencimiento(d["vencimiento_seguro"])
    txt, clr = color_indicador(ds, d["vencimiento_seguro"])
    val_seguro.config(text=txt, fg=clr)
    dv = funciones.verificar_vencimiento(d["vencimiento_vtv"])
    txt, clr = color_indicador(dv, d["vencimiento_vtv"])
    val_vtv.config(text=txt, fg=clr)
    kp = d["km_ultimo_cambio_aceite"] + d["frecuencia_aceite"]
    kr = kp - d["km_actual"]
    txt, clr = color_indicador(kr, "", es_km=True)
    val_aceite.config(text=txt, fg=clr)
    ch = obtener_chofer_activo(p, flota)
    val_chofer.config(text=ch if ch != "-" else "- Sin chofer -", fg="#75AADB" if ch != "-" else "#6B8AAB")
    lic = info_licencia(p, flota)
    if "VENC" in lic:
        val_licencia.config(text=lic, fg="#E74C3C")
    elif lic != "-":
        val_licencia.config(text=lic, fg="#2ECC71")
    else:
        val_licencia.config(text="-", fg="#6B8AAB")


# ============================================================
# ACTUALIZAR DASHBOARD: Actualiza todos los indicadores del panel de control
# cuando el usuario selecciona un vehiculo en la tabla.
# Obtiene la patente de la seleccion y delega en actualizar_dashboard_por_patente()
# ============================================================
def actualizar_dashboard_auto(event):
    sel = tabla.selection()
    if not sel: return
    p = tabla.item(sel[0])["values"][0]
    actualizar_dashboard_por_patente(p)


# ============================================================
# ACTUALIZAR TABLA: Refresca la tabla principal con todos los vehiculos
# Calcula finanzas (ingresos - gastos) y obtiene alertas de cada uno
# Alterna colores de filas (celeste/oscuro) para mejor legibilidad
# ============================================================
def actualizar_tabla():
    for fila in tabla.get_children():
        tabla.delete(fila)
    for idx, (patente, d) in enumerate(flota.items()):
        tg = calcular_gastos(d)
        bal = calcular_balance(d)
        tags = "fc" if idx % 2 == 0 else "fo"
        tabla.insert("", "end", values=(
            patente, d["modelo"], "{:,}km".format(d["km_actual"]),
            info_mata(patente, flota), obtener_chofer_activo(patente, flota),
            "${:,.0f}".format(d["ingresos"]), "${:,.0f}".format(tg),
            "${:,.0f}".format(bal), obtener_alertas(patente, d)
        ), tags=(tags,))


# ============================================================
# ALTERNAR CAMPO CONCEPTO: Habilita o deshabilita el campo de texto
# para gastos personalizados segun la categoria seleccionada
# ============================================================
def alt_concepto(event):
    if combo_categoria.get() == "5. Otro":
        entry_concepto.config(state="normal", bg="#13284D", fg="#FFFFFF")
    else:
        entry_concepto.delete(0, tk.END)
        entry_concepto.config(state="disabled", bg="#1A2D4A", fg="#6B8AAB")


# ============================================================
# GUARDAR MOVIMIENTO: Registra un ingreso o gasto para el vehiculo seleccionado
# Valida campos, suma al monto existente y actualiza la tabla/dashboard
# Soporta categorias: Combustible, Chofer, Seguro, Arreglos y Otros personalizados
# ============================================================
def guardar_mov():
    p = combo_autos.get()
    t = combo_tipo.get()
    ci = combo_categoria.get()
    ms = entry_monto.get()
    if not p or not t or not ms:
        messagebox.showerror("Error", "Complete todos los campos.")
        return
    try:
        m = float(ms)
    except:
        messagebox.showerror("Error", "Monto invalido.")
        return
    if t == "Ingreso":
        flota[p]["ingresos"] += m
    else:
        cats = {"1": "Combustible", "2": "Chofer", "3": "Seguro", "4": "Arreglos"}
        ok = False
        for k, v in cats.items():
            if k in ci:
                flota[p]["gastos_detalle"][v] += m
                ok = True
                break
        if not ok:
            if "5" in ci:
                c = entry_concepto.get().strip()
                if not c:
                    messagebox.showerror("Error", "Titulo requerido.")
                    return
                flota[p]["otros_gastos"][c] = flota[p]["otros_gastos"].get(c, 0) + m
            else:
                messagebox.showerror("Error", "Categoria invalida.")
                return
    datos.guardar_datos(flota)
    actualizar_tabla()
    actualizar_dashboard_por_patente(p)
    messagebox.showinfo("OK", "Movimiento registrado.")
    entry_monto.delete(0, tk.END)
    entry_concepto.delete(0, tk.END)
    entry_concepto.config(state="disabled", bg="#1A2D4A", fg="#6B8AAB")


# ============================================================
# DIALOGO AGREGAR VEHICULO: Abre una ventana modal para registrar un nuevo
# vehiculo en la flota. Solicita: patente, modelo, vencimientos, KM, etc.
# Valida que la patente no exista y que los KM sean numeros enteros.
# ============================================================
def dlg_agregar_veh():
    d = tk.Toplevel(ventana)
    d.title("Agregar Vehiculo")
    d.geometry("520x520")
    d.configure(bg="#0A1628")
    d.transient(ventana)
    d.grab_set()
    cv = tk.Canvas(d, bg="#0A1628", highlightthickness=0)
    sb = tk.Scrollbar(d, orient="vertical", command=cv.yview)
    fs = tk.Frame(cv, bg="#0A1628")
    fs.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.create_window((0, 0), window=fs, anchor="nw")
    cv.configure(yscrollcommand=sb.set)
    tk.Label(d, text="NUEVO VEHICULO", font=("Segoe UI", 14, "bold"),
             bg="#0A1628", fg="#F4D03F").pack(pady=12)
    campos = [
        ("Patente:", "pat"), ("Modelo:", "mod"),
        ("Facturacion:", "fac"), ("N Poliza:", "pol"),
        ("V Seguro:", "vs"), ("V VTV:", "vv"),
        ("V Matafuego:", "vm"), ("KM Actual:", "km"),
        ("KM Ult Aceite:", "ka"), ("Free Aceite(km):", "fa")
    ]
    en = {}
    for lb, k in campos:
        f = tk.Frame(fs, bg="#0A1628")
        f.pack(fill="x", padx=20, pady=3)
        tk.Label(f, text=lb, font=("Segoe UI", 10), bg="#0A1628", fg="#FFFFFF",
                 width=20, anchor="w").pack(side="left")
        e = tk.Entry(f, width=25, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        e.pack(side="right")
        en[k] = e
    en["fac"].insert(0, "Mensual")
    en["fa"].insert(0, "14000")
    cv.pack(side="left", fill="both", expand=True, padx=(0, 10))
    sb.pack(side="right", fill="y")

    def gv():
        dc = {k: en[k].get().strip() for k in en}
        for k, v in dc.items():
            if not v: messagebox.showerror("Error", "Campo vacio.", parent=d); return
        pat = dc["pat"].upper()
        if pat in flota: messagebox.showerror("Error", "Patente existe.", parent=d); return
        try: km, ka, fa = int(dc["km"]), int(dc["ka"]), int(dc["fa"])
        except: messagebox.showerror("Error", "KM deben ser enteros.", parent=d); return
        flota[pat] = {
            "modelo": dc["mod"], "facturacion": dc["fac"],
            "nro_poliza": dc["pol"], "vencimiento_seguro": dc["vs"],
            "vencimiento_vtv": dc["vv"], "vencimiento_matafuego": dc["vm"],
            "km_actual": km, "km_ultimo_cambio_aceite": ka,
            "frecuencia_aceite": fa, "ingresos": 0,
            "gastos_detalle": {"Combustible": 0, "Chofer": 0, "Seguro": 0, "Arreglos": 0},
            "otros_gastos": {}, "choferes": []
        }
        datos.guardar_datos(flota)
        actualizar_tabla()
        combo_autos.config(values=list(flota.keys()))
        d.destroy()
        messagebox.showinfo("OK", "Vehiculo " + pat + " agregado.")

    bf = tk.Frame(d, bg="#0A1628")
    bf.pack(fill="x", pady=10)
    tk.Button(bf, text="GUARDAR", bg="#2ECC71", fg="#000000",
              font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=5, command=gv).pack(side="left", padx=20, expand=True)
    tk.Button(bf, text="CANCELAR", bg="#E74C3C", fg="#FFFFFF",
              font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=5, command=d.destroy).pack(side="right", padx=20, expand=True)


# ============================================================
# DIALOGO EDITAR VEHICULO: Abre una ventana modal para modificar los datos
# de un vehiculo existente. Los campos se precargan con los valores actuales.
# La patente se muestra como texto fijo (no se puede cambiar).
# Preserva los datos financieros y choferes existentes.
# ============================================================
def dlg_editar_veh(patente_original):
    d_orig = flota[patente_original]
    d = tk.Toplevel(ventana)
    d.title("Editar Vehiculo")
    d.geometry("520x520")
    d.configure(bg="#0A1628")
    d.transient(ventana)
    d.grab_set()
    cv = tk.Canvas(d, bg="#0A1628", highlightthickness=0)
    sb = tk.Scrollbar(d, orient="vertical", command=cv.yview)
    fs = tk.Frame(cv, bg="#0A1628")
    fs.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.create_window((0, 0), window=fs, anchor="nw")
    cv.configure(yscrollcommand=sb.set)
    tk.Label(d, text="EDITAR VEHICULO", font=("Segoe UI", 14, "bold"),
             bg="#0A1628", fg="#F4D03F").pack(pady=12)

    # Campos a editar (patente se muestra pero no se puede cambiar)
    tk.Label(d, text="Patente: " + patente_original, font=("Segoe UI", 10, "bold"),
             bg="#0A1628", fg="#8AB4D6").pack(pady=2)

    campos = [
        ("Modelo:", "mod", d_orig["modelo"]),
        ("Facturacion:", "fac", d_orig["facturacion"]),
        ("N Poliza:", "pol", d_orig["nro_poliza"]),
        ("V Seguro (YYYY-MM-DD):", "vs", d_orig["vencimiento_seguro"]),
        ("V VTV (YYYY-MM-DD):", "vv", d_orig["vencimiento_vtv"]),
        ("V Matafuego (YYYY-MM-DD):", "vm", d_orig.get("vencimiento_matafuego", "")),
        ("KM Actual:", "km", str(d_orig["km_actual"])),
        ("KM Ult Aceite:", "ka", str(d_orig["km_ultimo_cambio_aceite"])),
        ("Free Aceite(km):", "fa", str(d_orig["frecuencia_aceite"])),
    ]
    en = {}
    for lb, k, val in campos:
        f = tk.Frame(fs, bg="#0A1628")
        f.pack(fill="x", padx=20, pady=3)
        tk.Label(f, text=lb, font=("Segoe UI", 10), bg="#0A1628", fg="#FFFFFF",
                 width=22, anchor="w").pack(side="left")
        e = tk.Entry(f, width=25, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        e.insert(0, val)
        e.pack(side="right")
        en[k] = e

    cv.pack(side="left", fill="both", expand=True, padx=(0, 10))
    sb.pack(side="right", fill="y")

    def gv():
        dc = {k: en[k].get().strip() for k in en}
        for k, v in dc.items():
            if not v:
                messagebox.showerror("Error", "Campo vacio.", parent=d)
                return
        try:
            km, ka, fa = int(dc["km"]), int(dc["ka"]), int(dc["fa"])
        except:
            messagebox.showerror("Error", "KM deben ser numeros enteros.", parent=d)
            return
        # Actualizar datos preservando ingresos/gastos/choferes
        flota[patente_original].update({
            "modelo": dc["mod"],
            "facturacion": dc["fac"],
            "nro_poliza": dc["pol"],
            "vencimiento_seguro": dc["vs"],
            "vencimiento_vtv": dc["vv"],
            "vencimiento_matafuego": dc["vm"],
            "km_actual": km,
            "km_ultimo_cambio_aceite": ka,
            "frecuencia_aceite": fa,
        })
        datos.guardar_datos(flota)
        actualizar_tabla()
        refrescar_seleccion(patente_original)
        d.destroy()
        messagebox.showinfo("OK", "Vehiculo " + patente_original + " actualizado.")

    bf = tk.Frame(d, bg="#0A1628")
    bf.pack(fill="x", pady=10)
    tk.Button(bf, text="GUARDAR CAMBIOS", bg="#75AADB", fg="#FFFFFF",
              font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=5, command=gv).pack(side="left", padx=20, expand=True)
    tk.Button(bf, text="CANCELAR", bg="#E74C3C", fg="#FFFFFF",
              font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=5, command=d.destroy).pack(side="right", padx=20, expand=True)


# ============================================================
# ELIMINAR VEHICULO: Borra permanentemente el vehiculo seleccionado
# Pide confirmacion al usuario antes de eliminar.
# Actualiza la tabla, el combo del formulario y el dashboard.
# ============================================================
def eliminar_vehiculo():
    sel = tabla.selection()
    if not sel:
        messagebox.showerror("Error", "Seleccione un vehiculo de la tabla.")
        return
    patente = tabla.item(sel[0])["values"][0]
    modelo = flota[patente]["modelo"]
    if messagebox.askyesno("Confirmar", "Eliminar " + patente + " (" + modelo + ")?\nSe borraran todos sus datos.", icon="warning"):
        del flota[patente]
        datos.guardar_datos(flota)
        actualizar_tabla()
        combo_autos.config(values=list(flota.keys()))
        # Limpiar dashboard
        lbl_dash_titulo.config(text="Seleccione vehiculo...")
        combo_autos.set("")
        messagebox.showinfo("OK", "Vehiculo " + patente + " eliminado.")


# ============================================================
# EDITAR VEHICULO SELECCIONADO: Obtiene la patente del vehiculo
# seleccionado en la tabla y abre el dialogo de edicion.
# ============================================================
def editar_vehiculo_seleccionado():
    sel = tabla.selection()
    if not sel:
        messagebox.showerror("Error", "Seleccione un vehiculo de la tabla.")
        return
    patente = tabla.item(sel[0])["values"][0]
    dlg_editar_veh(patente)


# ============================================================
# MENU CONTEXTUAL: Muestra un menu al hacer click derecho sobre un vehiculo
# en la tabla. Opciones: Editar, Eliminar, Gestionar Choferes.
# ============================================================
def mostrar_menu_contextual(event):
    item = tabla.identify_row(event.y)
    if item:
        tabla.selection_set(item)
        menu = tk.Menu(ventana, tearoff=0, bg="#0F1F3A", fg="#FFFFFF",
                       activebackground="#75AADB", activeforeground="#FFFFFF",
                       font=("Segoe UI", 9))
        menu.add_command(label="Editar Vehiculo", command=editar_vehiculo_seleccionado)
        menu.add_command(label="Eliminar Vehiculo", command=eliminar_vehiculo)
        menu.add_separator()
        menu.add_command(label="Gestionar Choferes", command=dlg_choferes)
        menu.post(event.x_root, event.y_root)


# ============================================================
# DIALOGO CHOFERES: Ventana principal de gestion de conductores.
# Permite: agregar nuevo chofer, editar datos, dar de alta/baja,
# eliminar chofer. Muestra estado de licencia y fechas de alta/baja.
# ============================================================
def dlg_choferes():
    d = tk.Toplevel(ventana)
    d.title("Choferes")
    d.geometry("700x500")
    d.configure(bg="#0A1628")
    d.transient(ventana)
    d.grab_set()
    tk.Label(d, text="CHOFERES", font=("Segoe UI", 14, "bold"),
             bg="#0A1628", fg="#F4D03F").pack(pady=10)
    fs = tk.Frame(d, bg="#0A1628")
    fs.pack(fill="x", padx=20, pady=5)
    tk.Label(fs, text="Vehiculo:", font=("Segoe UI", 10, "bold"),
             bg="#0A1628", fg="#FFFFFF").pack(side="left", padx=5)
    cv = ttk.Combobox(fs, values=list(flota.keys()), state="readonly", width=15)
    cv.pack(side="left", padx=5)
    if flota: cv.set(list(flota.keys())[0])
    ft = tk.Frame(d, bg="#0A1628")
    ft.pack(fill="both", expand=True, padx=20, pady=10)
    cols = ("Nombre", "Estado", "Vig. Licencia", "Fecha Alta", "Fecha Baja")
    tc = ttk.Treeview(ft, columns=cols, show="headings", height=8)
    anchos = {"Nombre": 140, "Estado": 80, "Vig. Licencia": 130, "Fecha Alta": 120, "Fecha Baja": 120}
    for c in cols:
        tc.heading(c, text=c)
        tc.column(c, width=anchos.get(c, 150), anchor="center")
    tc.tag_configure("fa", background="#1a3a1a", foreground="#2ECC71")
    tc.tag_configure("fb", background="#3a1a1a", foreground="#E74C3C")
    tc.pack(fill="both", expand=True, side="left")
    sc = tk.Scrollbar(ft, orient="vertical", command=tc.yview)
    sc.pack(side="right", fill="y")
    tc.configure(yscrollcommand=sc.set)

    # --------------------------------------------------------
    # CARGAR CHOFERES: Refresca la tabla de choferes del vehiculo seleccionado
    # Muestra nombre, estado (ALTA/BAJA), vigencia de licencia con alertas,
    # y fechas de alta/baja con colores verde (activo) y rojo (inactivo)
    # --------------------------------------------------------
    def cargar():
        for f in tc.get_children(): tc.delete(f)
        pt = cv.get()
        if pt and pt in flota:
            for c in flota[pt].get("choferes", []):
                est = "ALTA" if c["estado"] == "alta" else "BAJA"
                tag = "fa" if c["estado"] == "alta" else "fb"
                # Mostrar estado de la licencia
                lic = c.get("vigencia_licencia", "-")
                if c["estado"] == "alta" and lic != "-":
                    dl = funciones.verificar_vencimiento(lic)
                    if dl < 0:
                        lic = "VENC(" + str(abs(dl)) + "d)"
                    elif dl <= 30:
                        lic = str(dl) + "d"
                tc.insert("", "end", values=(
                    c["nombre"], est, lic,
                    c.get("fecha_alta", "-"),
                    c.get("fecha_baja", "-") if c["estado"] == "baja" else "-"
                ), tags=(tag,))

    tc.bind("<Double-1>", lambda e: editar_chofer() if tc.selection() else None)

    cv.bind("<<ComboboxSelected>>", lambda e: cargar())
    cargar()

    fb = tk.Frame(d, bg="#0A1628")
    fb.pack(fill="x", padx=20, pady=10)

    # --------------------------------------------------------
    # AGREGAR CHOFER: Abre un sub-dialogo para registrar un nuevo conductor
    # Solicita: nombre, vigencia de licencia y fecha de alta
    # Lo agrega con estado "alta" y guarda en el JSON
    # --------------------------------------------------------
    def agregar():
        pt = cv.get()
        if not pt: messagebox.showerror("Error", "Seleccione vehiculo.", parent=d); return
        s = tk.Toplevel(d)
        s.title("Nuevo Chofer")
        s.geometry("380x280")
        s.configure(bg="#0A1628")
        s.transient(d)
        s.grab_set()
        tk.Label(s, text="NUEVO CHOFER", font=("Segoe UI", 12, "bold"),
                 bg="#0A1628", fg="#F4D03F").pack(pady=8)
        tk.Label(s, text="Nombre:", bg="#0A1628", fg="#FFFFFF").pack()
        en = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        en.pack(pady=3)
        tk.Label(s, text="Vigencia Licencia (YYYY-MM-DD):", bg="#0A1628", fg="#FFFFFF").pack()
        el = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        el.insert(0, "2027-01-01")
        el.pack(pady=3)
        tk.Label(s, text="Fecha alta (YYYY-MM-DD):", bg="#0A1628", fg="#FFFFFF").pack()
        ef = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        ef.insert(0, date.today().isoformat())
        ef.pack(pady=3)

        def guardar():
            nom = en.get().strip()
            lic = el.get().strip()
            fec = ef.get().strip()
            if not nom: messagebox.showerror("Error", "Nombre obligatorio.", parent=s); return
            if not lic: lic = "2027-01-01"
            if "choferes" not in flota[pt]: flota[pt]["choferes"] = []
            flota[pt]["choferes"].append({
                "nombre": nom, "estado": "alta",
                "fecha_alta": fec, "fecha_baja": None,
                "vigencia_licencia": lic
            })
            datos.guardar_datos(flota)
            cargar()
            actualizar_tabla()
            refrescar_seleccion(pt)
            s.destroy()
            messagebox.showinfo("OK", "Chofer " + nom + " asignado.", parent=d)

        tk.Button(s, text="AGREGAR", bg="#2ECC71", fg="#000000",
                  font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=4, command=guardar).pack(pady=8)

    # --------------------------------------------------------
    # DAR DE BAJA: Cambia el estado del chofer a "baja" y registra
    # la fecha actual como fecha de baja. Actualiza tabla y dashboard.
    # --------------------------------------------------------
    def baja():
        pt = cv.get()
        if not pt or pt not in flota: return
        sel = tc.selection()
        if not sel: messagebox.showerror("Error", "Seleccione chofer.", parent=d); return
        nom = tc.item(sel[0])["values"][0]
        for c in flota[pt].get("choferes", []):
            if c["nombre"] == nom and c["estado"] == "alta":
                c["estado"] = "baja"
                c["fecha_baja"] = date.today().isoformat()
                datos.guardar_datos(flota)
                cargar()
                actualizar_tabla()
                refrescar_seleccion(pt)
                messagebox.showinfo("OK", nom + " dado de baja.", parent=d); return
        messagebox.showinfo("Info", "Ya esta de baja.", parent=d)

    # --------------------------------------------------------
    # DAR DE ALTA: Reactiva un chofer que estaba dado de baja.
    # Actualiza la fecha de alta a la fecha actual y limpia la fecha de baja.
    # --------------------------------------------------------
    def alta():
        pt = cv.get()
        if not pt or pt not in flota: return
        sel = tc.selection()
        if not sel: messagebox.showerror("Error", "Seleccione chofer.", parent=d); return
        nom = tc.item(sel[0])["values"][0]
        for c in flota[pt].get("choferes", []):
            if c["nombre"] == nom and c["estado"] == "baja":
                c["estado"] = "alta"
                c["fecha_alta"] = date.today().isoformat()
                c["fecha_baja"] = None
                datos.guardar_datos(flota)
                cargar()
                actualizar_tabla()
                refrescar_seleccion(pt)
                messagebox.showinfo("OK", nom + " dado de alta.", parent=d); return
        messagebox.showinfo("Info", "Ya esta activo.", parent=d)

    def editar_chofer():
        """Edita datos del chofer seleccionado (doble click)"""
        pt = cv.get()
        if not pt or pt not in flota: return
        sel = tc.selection()
        if not sel: return
        nom = tc.item(sel[0])["values"][0]
        # Buscar el chofer
        chofer_data = None
        for c in flota[pt].get("choferes", []):
            if c["nombre"] == nom:
                chofer_data = c
                break
        if not chofer_data: return

        s = tk.Toplevel(d)
        s.title("Editar Chofer")
        s.geometry("380x300")
        s.configure(bg="#0A1628")
        s.transient(d)
        s.grab_set()
        tk.Label(s, text="EDITAR CHOFER", font=("Segoe UI", 12, "bold"),
                 bg="#0A1628", fg="#F4D03F").pack(pady=8)
        tk.Label(s, text="Nombre:", bg="#0A1628", fg="#FFFFFF").pack()
        en = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        en.insert(0, chofer_data["nombre"])
        en.pack(pady=3)
        tk.Label(s, text="Vigencia Licencia (YYYY-MM-DD):", bg="#0A1628", fg="#FFFFFF").pack()
        el = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        el.insert(0, chofer_data.get("vigencia_licencia", "2027-01-01"))
        el.pack(pady=3)
        tk.Label(s, text="Fecha alta (YYYY-MM-DD):", bg="#0A1628", fg="#FFFFFF").pack()
        ef = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
        ef.insert(0, chofer_data.get("fecha_alta", date.today().isoformat()))
        ef.pack(pady=3)
        if chofer_data["estado"] == "baja":
            tk.Label(s, text="Fecha baja (YYYY-MM-DD):", bg="#0A1628", fg="#FFFFFF").pack()
            eb = tk.Entry(s, width=30, bg="#13284D", fg="#FFFFFF", bd=1, relief="solid")
            eb.insert(0, chofer_data.get("fecha_baja", ""))
            eb.pack(pady=3)
        else:
            eb = None

        def guardar():
            nom_nuevo = en.get().strip()
            if not nom_nuevo:
                messagebox.showerror("Error", "Nombre obligatorio.", parent=s)
                return
            chofer_data["nombre"] = nom_nuevo
            chofer_data["vigencia_licencia"] = el.get().strip() or "2027-01-01"
            chofer_data["fecha_alta"] = ef.get().strip() or date.today().isoformat()
            if eb is not None:
                chofer_data["fecha_baja"] = eb.get().strip() or None
            datos.guardar_datos(flota)
            cargar()
            actualizar_tabla()
            refrescar_seleccion(pt)
            s.destroy()
            messagebox.showinfo("OK", "Chofer " + nom_nuevo + " actualizado.", parent=d)

        tk.Button(s, text="GUARDAR", bg="#75AADB", fg="#FFFFFF",
                  font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=4, command=guardar).pack(pady=8)

    # --------------------------------------------------------
    # ELIMINAR CHOFER: Borra permanentemente el chofer seleccionado
    # Pide confirmacion antes de eliminar. Actualiza tabla y dashboard.
    # --------------------------------------------------------
    def elim():
        pt = cv.get()
        if not pt or pt not in flota: return
        sel = tc.selection()
        if not sel: return
        nom = tc.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", "Eliminar a " + nom + "?", parent=d):
            flota[pt]["choferes"] = [c for c in flota[pt].get("choferes", []) if c["nombre"] != nom]
            datos.guardar_datos(flota)
            cargar(); actualizar_tabla()
            refrescar_seleccion(pt)
            messagebox.showinfo("OK", "Eliminado.", parent=d)

    bs = {"font": ("Segoe UI", 9, "bold"), "bd": 0, "padx": 10, "pady": 4, "cursor": "hand2"}
    tk.Button(fb, text="Nuevo", bg="#2ECC71", fg="#000000", **bs, command=agregar).pack(side="left", padx=2)
    tk.Button(fb, text="Editar", bg="#75AADB", fg="#FFFFFF", **bs, command=editar_chofer).pack(side="left", padx=2)
    tk.Button(fb, text="Baja", bg="#E74C3C", fg="#FFFFFF", **bs, command=baja).pack(side="left", padx=2)
    tk.Button(fb, text="Alta", bg="#2ECC71", fg="#000000", **bs, command=alta).pack(side="left", padx=2)
    tk.Button(fb, text="Elim", bg="#7F8C8D", fg="#FFFFFF", **bs, command=elim).pack(side="left", padx=2)
    tk.Button(d, text="CERRAR", bg="#2A4A6A", fg="#FFFFFF",
              font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=4, command=d.destroy).pack(pady=6)


# ============================================================
# ALERTAS DE INICIO: Escanea todos los vehiculos al arrancar el programa
# y muestra un dialogo con los vencimientos proximos (seguro, VTV,
# matafuego, aceite, licencia). Ordena por urgencia: vencidos primero.
# Si no hay alertas, no muestra nada.
# ============================================================
def mostrar_alertas_inicio():
    items = []  # (patente, modelo, icono, texto, dias, gravedad)

    for patente, d in flota.items():
        modelo = d["modelo"]

        # Seguro (alerta si <= 30 dias)
        ds = funciones.verificar_vencimiento(d["vencimiento_seguro"])
        if ds < 0:
            items.append((patente, modelo, "SEGURO", "VENCIDO hace " + str(abs(ds)) + " dias", ds, "rojo"))
        elif ds <= 30:
            items.append((patente, modelo, "SEGURO", "Vence en " + str(ds) + " dias", ds, "naranja"))

        # VTV (alerta si <= 30 dias)
        dv = funciones.verificar_vencimiento(d["vencimiento_vtv"])
        if dv < 0:
            items.append((patente, modelo, "VTV", "VENCIDA hace " + str(abs(dv)) + " dias", dv, "rojo"))
        elif dv <= 30:
            items.append((patente, modelo, "VTV", "Vence en " + str(dv) + " dias", dv, "naranja"))

        # Matafuego (alerta si <= 30 dias)
        if "vencimiento_matafuego" in d:
            dm = funciones.verificar_vencimiento(d["vencimiento_matafuego"])
            if dm < 0:
                items.append((patente, modelo, "MATAFUEGO", "VENCIDO hace " + str(abs(dm)) + " dias", dm, "rojo"))
            elif dm <= 30:
                items.append((patente, modelo, "MATAFUEGO", "Vence en " + str(dm) + " dias", dm, "naranja"))

        # Aceite (alerta si km restantes <= 1500)
        kp = d["km_ultimo_cambio_aceite"] + d["frecuencia_aceite"]
        kr = kp - d["km_actual"]
        if kr <= 0:
            items.append((patente, modelo, "ACEITE", "PASADO por " + str(abs(kr)) + " km", -999, "rojo"))
        elif kr <= 1500:
            items.append((patente, modelo, "ACEITE", "Quedan " + str(kr) + " km", kr, "naranja"))

        # Licencia de chofer activo (alerta si <= 30 dias)
        if "choferes" in d:
            for c in d["choferes"]:
                if c["estado"] == "alta" and "vigencia_licencia" in c:
                    dl = funciones.verificar_vencimiento(c["vigencia_licencia"])
                    if dl < 0:
                        items.append((patente, modelo, "LICENCIA", c["nombre"] + " VENCIDA hace " + str(abs(dl)) + " dias", dl, "rojo"))
                    elif dl <= 30:
                        items.append((patente, modelo, "LICENCIA", c["nombre"] + " vence en " + str(dl) + " dias", dl, "naranja"))
                    break

    if not items:
        return  # Todo en orden, no mostrar nada

    # Ordenar: primero las vencidas (rojo), luego las mas urgentes
    items.sort(key=lambda x: (0 if x[4] < 0 else 1, x[4]))

    # Crear dialogo
    dlg = tk.Toplevel(ventana)
    dlg.title("ALERTAS DE VENCIMIENTO")
    dlg.geometry("650x450")
    dlg.configure(bg="#0A1628")
    dlg.transient(ventana)
    dlg.grab_set()

    # Titulo
    total_alarmas = len([i for i in items if i[5] == "rojo"])
    total_preven = len([i for i in items if i[5] == "naranja"])
    color_titulo = "#E74C3C" if total_alarmas > 0 else "#F39C12"
    tk.Label(dlg, text="ALERTAS DE VENCIMIENTO", font=("Segoe UI", 16, "bold"),
             bg="#0A1628", fg=color_titulo).pack(pady=(12, 2))
    tk.Label(dlg, text=str(total_alarmas) + " vencidas  |  " + str(total_preven) + " proximas a vencer",
             font=("Segoe UI", 10), bg="#0A1628", fg="#8AB4D6").pack(pady=(0, 8))

    # Frame con scroll para la lista
    frame_lista = tk.Frame(dlg, bg="#0F1F3A", bd=1, relief="solid")
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    canvas = tk.Canvas(frame_lista, bg="#0F1F3A", highlightthickness=0)
    scrollbar = tk.Scrollbar(frame_lista, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#0F1F3A")
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Agrupar items por patente
    grupos = {}
    for item in items:
        key = item[0]
        if key not in grupos:
            grupos[key] = {"modelo": item[1], "items": []}
        grupos[key]["items"].append(item)

    for patente, grupo in grupos.items():
        # Encabezado del vehiculo
        hdr = tk.Frame(scroll_frame, bg="#060D20", bd=1, relief="solid")
        hdr.pack(fill="x", padx=5, pady=(4, 0))
        tk.Label(hdr, text="  " + patente + "  -  " + grupo["modelo"],
                 font=("Segoe UI", 10, "bold"), bg="#060D20", fg="#F4D03F",
                 anchor="w", padx=8).pack(anchor="w", pady=3)

        for item in grupo["items"]:
            icono, texto, gravedad = item[2], item[3], item[5]
            bg_item = "#2C0C0C" if gravedad == "rojo" else "#2C2000"
            fg_item = "#E74C3C" if gravedad == "rojo" else "#F39C12"

            fila = tk.Frame(scroll_frame, bg=bg_item, bd=0)
            fila.pack(fill="x", padx=10, pady=1)

            lbl_icono = tk.Label(fila, text=icono, font=("Consolas", 9, "bold"),
                                  bg=bg_item, fg=fg_item, width=12, anchor="w")
            lbl_icono.pack(side="left", padx=(8, 0), pady=2)

            lbl_texto = tk.Label(fila, text=texto, font=("Consolas", 9),
                                  bg=bg_item, fg="#FFFFFF", anchor="w")
            lbl_texto.pack(side="left", padx=5, pady=2)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Boton inferior
    btn_frame = tk.Frame(dlg, bg="#0A1628")
    btn_frame.pack(fill="x", pady=10)
    tk.Button(btn_frame, text="ENTENDIDO", bg="#F4D03F", fg="#000000",
              font=("Segoe UI", 10, "bold"), bd=0, padx=30, pady=5,
              activebackground="#D4AC0D", cursor="hand2",
              command=dlg.destroy).pack()


# ============================================================
# VENTANA PRINCIPAL: Configuracion inicial de la interfaz
# Tamaño: 1100x780, fondo negro, estilo oscuro profesional
# ============================================================
ventana = tk.Tk()
ventana.title("Control Flota Profesional")
ventana.geometry("1100x780")
ventana.configure(bg="#050B1A")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview.Heading", background="#0F1F3A", foreground="#F4D03F",
                font=("Segoe UI", 10, "bold"))
style.configure("Treeview", rowheight=30, font=("Consolas", 9),
                background="#050B1A", fieldbackground="#050B1A")

# ============================================================
# BARRA DE HERRAMIENTAS: Botones de accion principal
# AGREGAR VEHICULO (verde), EDITAR (azul), ELIMINAR (rojo),
# GESTIONAR CHOFERES (morado)
# ============================================================
tb = tk.Frame(ventana, bg="#060D20", height=50)
tb.pack(fill="x")
tk.Label(tb, text="CONTROL DE FLOTA PROFESIONAL",
         font=("Segoe UI", 16, "bold"), bg="#060D20", fg="#F4D03F").pack(side="left", padx=15, pady=10)
tk.Button(tb, text="AGREGAR VEHICULO", bg="#2ECC71", fg="#000000",
          font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=6,
          activebackground="#27AE60", cursor="hand2",
          command=dlg_agregar_veh).pack(side="right", padx=5, pady=8)
tk.Button(tb, text="EDITAR VEHICULO", bg="#75AADB", fg="#FFFFFF",
          font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=6,
          activebackground="#4A90C4", cursor="hand2",
          command=editar_vehiculo_seleccionado).pack(side="right", padx=3, pady=8)
tk.Button(tb, text="ELIMINAR VEHICULO", bg="#E74C3C", fg="#FFFFFF",
          font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=6,
          activebackground="#C0392B", cursor="hand2",
          command=eliminar_vehiculo).pack(side="right", padx=3, pady=8)
tk.Button(tb, text="GESTIONAR CHOFERES", bg="#F4D03F", fg="#000000",
          font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=6,
          activebackground="#D4AC0D", cursor="hand2",
          command=dlg_choferes).pack(side="right", padx=5, pady=8)

# ============================================================
# TABLA PRINCIPAL: Lista todos los vehiculos con sus indicadores
# Columnas: Patente, Modelo, KM, Matafuego, Chofer, Ingresos,
# Gastos, Balance, Alertas. Soporta click derecho y doble click.
# ============================================================
cols = ("Patente", "Modelo", "KM", "Matafuego", "Chofer", "Ingresos", "Gastos", "Balance", "Alertas")
tabla = ttk.Treeview(ventana, columns=cols, show="headings", height=5)
for c in cols:
    tabla.heading(c, text=c)
    tabla.column(c, width=120, anchor="center")
tabla.tag_configure("fc", background="#75AADB", foreground="#FFFFFF")
tabla.tag_configure("fo", background="#13284D", foreground="#FFFFFF")
tabla.pack(padx=15, pady=(10, 5), fill="x")
tabla.bind("<<TreeviewSelect>>", actualizar_dashboard_auto)
tabla.bind("<Button-3>", mostrar_menu_contextual)
tabla.bind("<Double-1>", lambda e: editar_vehiculo_seleccionado() if tabla.selection() else None)

# ============================================================
# PANEL DE CONTROL: Muestra indicadores detallados del vehiculo seleccionado
# Incluye: ingresos, gastos, balance, conductor activo,
# y estado de vencimientos (matafuego, seguro, VTV, aceite, licencia)
# ============================================================
fd = tk.LabelFrame(ventana, text=" Panel de Control ",
                   font=("Segoe UI", 11, "bold"), bg="#0A1628",
                   fg="#FFFFFF", bd=1, relief="solid")
fd.pack(padx=15, pady=8, fill="x")
lbl_dash_titulo = tk.Label(fd, text="Seleccione vehiculo...",
                           font=("Segoe UI", 11, "italic"),
                           bg="#0A1628", fg="#FFFFFF")
lbl_dash_titulo.pack(pady=5)

# ------------------------------------------------------------
# TARJETAS FINANCIERAS: Muestran ingresos, gastos, balance y conductor
# Con colores distintivos: celste (ingresos), gris (gastos),
# negro (balance), azul oscuro (conductor)
# ------------------------------------------------------------
ft1 = tk.Frame(fd, bg="#0A1628")
ft1.pack(pady=(5, 2))

def tcard(p, color, ancho=180):
    t = tk.Frame(p, bg=color, bd=1, relief="solid", width=ancho, height=65)
    t.pack_propagate(False)
    t.pack(side="left", padx=8)
    return t

t1 = tcard(ft1, "#75AADB")
tk.Label(t1, text="FACTURADO", font=("Segoe UI", 8, "bold"), bg="#75AADB", fg="#FFFFFF").pack(pady=2)
val_ingresos = tk.Label(t1, text="$0", font=("Consolas", 13, "bold"), bg="#75AADB", fg="#FFFFFF")
val_ingresos.pack()

t2 = tcard(ft1, "#1A2D4A")
tk.Label(t2, text="GASTOS", font=("Segoe UI", 8, "bold"), bg="#1A2D4A", fg="#FFFFFF").pack(pady=2)
val_gastos = tk.Label(t2, text="$0", font=("Consolas", 13, "bold"), bg="#1A2D4A", fg="#FFFFFF")
val_gastos.pack()

t3 = tcard(ft1, "#050B1A", 180)
tk.Label(t3, text="BALANCE", font=("Segoe UI", 8, "bold"), bg="#050B1A", fg="#F4D03F").pack(pady=2)
val_balance = tk.Label(t3, text="$0", font=("Consolas", 13, "bold"), bg="#050B1A", fg="#F4D03F")
val_balance.pack()

t4 = tcard(ft1, "#0F1F3A", 180)
tk.Label(t4, text="CONDUCTOR", font=("Segoe UI", 8, "bold"), bg="#0F1F3A", fg="#FFFFFF").pack(pady=2)
val_chofer = tk.Label(t4, text="-", font=("Consolas", 11, "bold"), bg="#0F1F3A", fg="#8AB4D6")
val_chofer.pack()

# ------------------------------------------------------------
# INDICADORES DE VENCIMIENTO: Muestran el estado de cada vencimiento
# Matafuego, Seguro, VTV, Aceite y Licencia con colores de alerta
# Verde = vigente, Naranja = proximo a vencer, Rojo = vencido
# ------------------------------------------------------------
ft2 = tk.Frame(fd, bg="#0A1628")
ft2.pack(pady=(2, 8))

def ind(p, txt, ancho=150):
    f = tk.Frame(p, bg="#0F1F3A", bd=1, relief="solid", width=ancho, height=55)
    f.pack_propagate(False)
    f.pack(side="left", padx=6)
    tk.Label(f, text=txt, font=("Segoe UI", 7, "bold"), bg="#0F1F3A", fg="#8AB4D6").pack(pady=1)
    v = tk.Label(f, text="-", font=("Consolas", 10, "bold"), bg="#0F1F3A", fg="#FFFFFF")
    v.pack()
    return v

val_matafuego = ind(ft2, "MATAFUEGO")
val_seguro = ind(ft2, "SEGURO")
val_vtv = ind(ft2, "VTV")
val_aceite = ind(ft2, "ACEITE")
val_licencia = ind(ft2, "LICENCIA")

# ============================================================
# FORMULARIO DE REGISTRO: Permite registrar ingresos y gastos
# Selecciona: vehiculo, tipo (ingreso/gasto), categoria,
# concepto personalizado (opcional) y monto
# ============================================================
ff = tk.LabelFrame(ventana, text=" Registro ",
                   font=("Segoe UI", 11, "bold"), bg="#0A1628",
                   fg="#FFFFFF", bd=1, relief="solid")
ff.pack(padx=15, pady=8, fill="x")
gf = tk.Frame(ff, bg="#0A1628")
gf.pack(pady=6)

def lb(t, r, c):
    tk.Label(gf, text=t, font=("Segoe UI", 10),
             bg="#0A1628", fg="#FFFFFF").grid(row=r, column=c, sticky="w", padx=4, pady=2)

lb("Auto:", 0, 0)
combo_autos = ttk.Combobox(gf, values=list(flota.keys()), state="readonly", width=14)
combo_autos.grid(row=0, column=1, padx=2, pady=2)
lb("Tipo:", 0, 2)
combo_tipo = ttk.Combobox(gf, values=["Ingreso", "Gasto"], state="readonly", width=14)
combo_tipo.grid(row=0, column=3, padx=2, pady=2)
lb("Categoria:", 0, 4)
cats = ["1. Combustible", "2. Chofer", "3. Seguro", "4. Arreglos", "5. Otro"]
combo_categoria = ttk.Combobox(gf, values=cats, state="readonly", width=20)
combo_categoria.grid(row=0, column=5, padx=2, pady=2)
combo_categoria.bind("<<ComboboxSelected>>", alt_concepto)
lb("Concepto:", 1, 0)
entry_concepto = tk.Entry(gf, width=18, state="disabled", bg="#1A2D4A",
                          fg="#6B8AAB", bd=1, relief="solid")
entry_concepto.grid(row=1, column=1, padx=2, pady=2)
lb("Monto ($):", 1, 2)
entry_monto = tk.Entry(gf, width=14, bg="#13284D", fg="#FFFFFF",
                        bd=1, relief="solid")
entry_monto.grid(row=1, column=3, padx=2, pady=2)
tk.Button(gf, text="REGISTRAR", bg="#F4D03F", fg="#000000",
          font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=4,
          activebackground="#D4AC0D", cursor="hand2",
          command=guardar_mov).grid(row=1, column=4, columnspan=2, padx=4, pady=2, sticky="ew")

actualizar_tabla()
# Mostrar alertas de vencimiento al iniciar (despues de que la ventana este lista)
ventana.after(500, mostrar_alertas_inicio)
ventana.mainloop()