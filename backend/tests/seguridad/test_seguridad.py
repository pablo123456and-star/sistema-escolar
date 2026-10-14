"""Pruebas del paquete seguridad: CU01 (sesión, bloqueo e intentos fallidos, recuperación por correo), CU02 (usuarios), CU03 (roles) y CU04 (bitácora)."""
from datetime import UTC, datetime, timedelta
from sqlalchemy import select, update
from app.paquetes.seguridad.models import TokenRecuperacion, Usuario
from app.nucleo.seguridad import hashear_token
from tests.conftest import iniciar


# ---- CU01 ---------------------------------------------------------------------
async def test_cu01_inicia_sesion_con_usuario_o_correo(cliente):
    r = await cliente.post("/seguridad/sesion", json={"identificador": "DIRECCION", "contrasena": "Escuela2026"})
    assert r.status_code == 200
    datos = r.json()
    assert datos["token"] and datos["usuario"]["rol"] == "administrador"
    assert datos["usuario"]["ultimo_acceso"] is not None

    # También debe permitir iniciar sesión ingresando el correo electrónico
    r_correo = await cliente.post("/seguridad/sesion", json={"identificador": "direccion@escuelamodelo.edu.bo", "contrasena": "Escuela2026"})
    assert r_correo.status_code == 200
    assert r_correo.json()["token"]


async def test_cu01_mismo_mensaje_si_falla_usuario_o_contrasena(cliente):
    r1 = await cliente.post("/seguridad/sesion", json={"identificador": "direccion", "contrasena": "otra123"})
    r2 = await cliente.post("/seguridad/sesion", json={"identificador": "noexiste", "contrasena": "otra123"})
    assert r1.status_code == r2.status_code == 400
    assert r1.json()["detalle"] == r2.json()["detalle"] == "Usuario o contraseña incorrectos."


async def test_cu01_cuenta_inactiva_no_ingresa(cliente, admin):
    r = await cliente.patch("/seguridad/usuarios/4", json={"estado_usuario": "bloqueado"}, headers=admin)
    assert r.status_code == 200
    r = await cliente.post("/seguridad/sesion", json={"identificador": "rflores", "contrasena": "Escuela2026"})
    assert r.status_code == 400 and r.json()["codigo"] == "cuenta_inactiva"


async def test_cu01_token_requerido_y_valido(cliente):
    assert (await cliente.get("/seguridad/perfil")).status_code == 401
    r = await cliente.get("/seguridad/perfil", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401


async def test_cu01_token_de_cuenta_desactivada_deja_de_servir(cliente, admin, profesor):
    assert (await cliente.get("/seguridad/perfil", headers=profesor)).status_code == 200
    await cliente.patch("/seguridad/usuarios/4", json={"estado_usuario": "inactivo"}, headers=admin)
    assert (await cliente.get("/seguridad/perfil", headers=profesor)).status_code == 401


async def test_cu01_cambiar_contrasena_propia(cliente, profesor):
    # Contraseña actual incorrecta
    r = await cliente.post("/seguridad/perfil/contrasena", json={"actual": "mala", "nueva": "Nueva2026*"}, headers=profesor)
    assert r.status_code == 400

    # Nueva contraseña sin número o sin caracter especial (falla política)
    r = await cliente.post("/seguridad/perfil/contrasena", json={"actual": "Escuela2026", "nueva": "sololetras"},
                           headers=profesor)
    assert r.status_code == 422
    r = await cliente.post("/seguridad/perfil/contrasena", json={"actual": "Escuela2026", "nueva": "SinEspecial2026"},
                           headers=profesor)
    assert r.status_code == 422

    # Cambio exitoso cumpliendo todos los requisitos
    r = await cliente.post("/seguridad/perfil/contrasena", json={"actual": "Escuela2026", "nueva": "Nueva2026*"},
                           headers=profesor)
    assert r.status_code == 200
    await iniciar(cliente, "rflores", "Nueva2026*")


async def test_cu01_tres_intentos_fallidos_bloquean_cuenta(cliente):
    # Intento 1: falla con mensaje genérico
    r1 = await cliente.post("/seguridad/sesion", json={"identificador": "marioq", "contrasena": "erronea1"})
    assert r1.status_code == 400
    assert r1.json()["detalle"] == "Usuario o contraseña incorrectos."

    # Intento 2: falla con mensaje genérico
    r2 = await cliente.post("/seguridad/sesion", json={"identificador": "marioq", "contrasena": "erronea2"})
    assert r2.status_code == 400
    assert r2.json()["detalle"] == "Usuario o contraseña incorrectos."

    # Intento 3: se bloquea por 5 minutos
    r3 = await cliente.post("/seguridad/sesion", json={"identificador": "marioq", "contrasena": "erronea3"})
    assert r3.status_code == 400
    datos3 = r3.json()
    assert datos3["codigo"] == "cuenta_bloqueada"
    assert "Cuenta bloqueada temporalmente" in datos3["detalle"]
    assert "esperar" in datos3["detalle"].lower()

    # Intento 4 mientras dura el bloqueo (incluso con la contraseña correcta): sigue bloqueada
    r4 = await cliente.post("/seguridad/sesion", json={"identificador": "marioq", "contrasena": "Escuela2026"})
    assert r4.status_code == 400
    assert r4.json()["codigo"] == "cuenta_bloqueada"
    assert "Cuenta bloqueada temporalmente" in r4.json()["detalle"]


async def test_cu01_login_exitoso_restablece_contador_fallos(cliente):
    # Falla 2 veces (menos de 3)
    await cliente.post("/seguridad/sesion", json={"identificador": "erojas", "contrasena": "erronea1"})
    await cliente.post("/seguridad/sesion", json={"identificador": "erojas", "contrasena": "erronea2"})

    # Inicia sesión correctamente
    r_ok = await cliente.post("/seguridad/sesion", json={"identificador": "erojas", "contrasena": "Escuela2026"})
    assert r_ok.status_code == 200

    # Un nuevo intento fallido NO debe bloquear la cuenta porque el contador volvió a cero
    r_nuevo = await cliente.post("/seguridad/sesion", json={"identificador": "erojas", "contrasena": "erronea3"})
    assert r_nuevo.status_code == 400
    assert r_nuevo.json()["codigo"] == "credenciales"


async def test_cu01_recuperacion_por_correo_flujo_completo(cliente):
    # 1. Solicitud con correo registrado
    r_reg = await cliente.post("/seguridad/recuperar-contrasena", json={"correo": "eljhonita69@gmail.com"})
    assert r_reg.status_code == 200

    # 2. Solicitud con correo inexistente: misma respuesta genérica (anti-enumeración)
    r_no = await cliente.post("/seguridad/recuperar-contrasena", json={"correo": "noexiste@correo.com"})
    assert r_no.status_code == 200
    assert r_reg.json() == r_no.json()

    # 3. Validar token inexistente o inválido
    r_inv = await cliente.get("/seguridad/recuperar-contrasena/validar", params={"token": "token-falso-inexistente"})
    assert r_inv.status_code == 200 and r_inv.json()["valido"] is False

    # 4. En el caso de uso se generó un token en token_recuperacion para un usuario.
    # Simulamos el token para probar validación y restablecimiento
    from app.nucleo.seguridad import generar_token_recuperacion
    token_plano, token_hash = generar_token_recuperacion()
    from app.nucleo import bd
    async with bd._fabrica() as s:
        tk = TokenRecuperacion(
            id_usuario=5,  # mquispe
            token_hash=token_hash,
            expira_en=datetime.now(UTC) + timedelta(minutes=15),
        )
        s.add(tk)
        await s.commit()

    # 5. Validar el token real
    r_val = await cliente.get("/seguridad/recuperar-contrasena/validar", params={"token": token_plano})
    assert r_val.status_code == 200
    assert r_val.json()["valido"] is True
    assert r_val.json()["nombre_usuario"] == "mquispe"

    # 6. Intentar restablecer con contraseña débil (sin caracteres especiales)
    r_debil = await cliente.post("/seguridad/restablecer-contrasena", json={"token": token_plano, "nueva": "Clave1234"})
    assert r_debil.status_code == 422

    # 7. Restablecer con contraseña segura
    r_rest = await cliente.post("/seguridad/restablecer-contrasena", json={"token": token_plano, "nueva": "Colegio2026*!"})
    assert r_rest.status_code == 200
    assert "exitosamente" in r_rest.json()["mensaje"]

    # 8. Token de un solo uso: no se puede volver a utilizar
    r_reuso = await cliente.get("/seguridad/recuperar-contrasena/validar", params={"token": token_plano})
    assert r_reuso.status_code == 200 and r_reuso.json()["valido"] is False

    # 9. Iniciar sesión con la nueva contraseña funciona
    r_login = await cliente.post("/seguridad/sesion", json={"identificador": "mquispe", "contrasena": "Colegio2026*!"})
    assert r_login.status_code == 200

    # 10. La contraseña anterior ya no funciona
    r_antigua = await cliente.post("/seguridad/sesion", json={"identificador": "mquispe", "contrasena": "Escuela2026"})
    assert r_antigua.status_code == 400


async def test_cu01_panel_inicio(cliente, admin, profesor):
    r = (await cliente.get("/seguridad/inicio", headers=admin)).json()
    assert r["estudiantes_activos"] == 12 and r["actividades"]
    r = (await cliente.get("/seguridad/inicio", headers=profesor)).json()
    assert r["actividades"] == []


# ---- CU02 ---------------------------------------------------------------------
async def test_cu02_solo_administrador(cliente, profesor):
    assert (await cliente.get("/seguridad/usuarios", headers=profesor)).status_code == 403


async def test_cu02_listar_con_filtros(cliente, admin):
    r = (await cliente.get("/seguridad/usuarios", params={"id_rol": 2}, headers=admin)).json()
    assert r["total"] == 2 and {u["nombre_rol"] for u in r["items"]} == {"profesor"}
    r = (await cliente.get("/seguridad/usuarios", params={"q": "flores"}, headers=admin)).json()
    assert [u["nombre_usuario"] for u in r["items"]] == ["rflores"]


async def test_cu02_crear_usuario_respeta_especializacion(cliente, admin):
    roles = {r["nombre_rol"]: r["id_rol"] for r in (await cliente.get("/seguridad/roles", headers=admin)).json()}
    candidatos = (await cliente.get("/seguridad/usuarios/personas-sin-cuenta",
                                    params={"id_rol": roles["tutor"]}, headers=admin)).json()
    ci = candidatos[0]["ci"]

    r = await cliente.post("/seguridad/usuarios", headers=admin, json={
        "ci_persona": ci, "id_rol": roles["profesor"], "nombre_usuario": "tutor.nuevo", "contrasena": "Clave2026*"})
    assert r.status_code == 400 and "docente" in r.json()["detalle"]

    r = await cliente.post("/seguridad/usuarios", headers=admin, json={
        "ci_persona": ci, "id_rol": roles["tutor"], "nombre_usuario": "tutor.nuevo", "contrasena": "Clave2026*"})
    assert r.status_code == 201 and r.json()["nombre_rol"] == "tutor"
    await iniciar(cliente, "tutor.nuevo", "Clave2026*")

    r = await cliente.post("/seguridad/usuarios", headers=admin, json={
        "ci_persona": ci, "id_rol": roles["tutor"], "nombre_usuario": "otro.nombre", "contrasena": "Clave2026*"})
    assert r.status_code == 409 and r.json()["detalle"] == "La persona ya tiene una cuenta de usuario."


async def test_cu02_nombre_usuario_duplicado(cliente, admin):
    r = await cliente.patch("/seguridad/usuarios/4", json={"nombre_usuario": "erojas"}, headers=admin)
    assert r.status_code == 409 and r.json()["detalle"] == "El nombre de usuario ya está en uso."


async def test_cu02_no_puede_desactivarse_a_si_mismo(cliente, admin):
    r = await cliente.delete("/seguridad/usuarios/2", headers=admin)
    assert r.status_code == 400
    r = await cliente.delete("/seguridad/usuarios/4", headers=admin)
    assert r.status_code == 200 and r.json()["estado_usuario"] == "inactivo"


# ---- CU03 ---------------------------------------------------------------------
async def test_cu03_roles_y_permisos(cliente, admin):
    roles = (await cliente.get("/seguridad/roles", headers=admin)).json()
    assert [r["nombre_rol"] for r in roles] == ["administrador", "profesor", "estudiante", "tutor"]
    r = await cliente.patch(f"/seguridad/roles/{roles[1]['id_rol']}", json={"descripcion_rol": "Docentes"}, headers=admin)
    assert r.json()["descripcion_rol"] == "Docentes"
    permisos = (await cliente.get("/seguridad/permisos", headers=admin)).json()
    assert len(permisos) == 27


async def test_cu03_asignar_rol_valida_persona(cliente, admin):
    roles = {r["nombre_rol"]: r["id_rol"] for r in (await cliente.get("/seguridad/roles", headers=admin)).json()}
    r = await cliente.patch("/seguridad/usuarios/4/rol", json={"id_rol": roles["tutor"]}, headers=admin)
    assert r.status_code == 400
    r = await cliente.patch("/seguridad/usuarios/2/rol", json={"id_rol": roles["profesor"]}, headers=admin)
    assert r.status_code == 400 and "propia" in r.json()["detalle"]


# ---- CU04 ---------------------------------------------------------------------
async def test_cu04_bitacora_filtra_y_oculta_contrasenas(cliente, admin):
    await cliente.post("/seguridad/usuarios/4/restablecer-contrasena", headers=admin)
    r = (await cliente.get("/seguridad/bitacora", params={"tabla": "usuario", "tamano": 5}, headers=admin)).json()
    assert r["total"] > 0
    for fila in r["items"]:
        for datos in (fila["datos_anteriores"], fila["datos_nuevos"]):
            if datos and "password_hash" in datos:
                assert datos["password_hash"] == "********"
    ultima = r["items"][0]
    assert ultima["nombre_usuario"] == "direccion" and ultima["ip"]

    r = await cliente.get("/seguridad/bitacora", params={"desde": "2026-12-01", "hasta": "2026-01-01"}, headers=admin)
    assert r.status_code == 400
    opciones = (await cliente.get("/seguridad/bitacora/opciones", headers=admin)).json()
    assert "SEGURIDAD" in opciones["modulos"]
