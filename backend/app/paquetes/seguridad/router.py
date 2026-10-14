"""
Endpoints del paquete seguridad: /api/v1/seguridad/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request, status

from app.nucleo.dependencias import Administrador, Sesion, Usuario
from app.nucleo.esquemas import Mensaje, NumeroPagina, Pagina, TamanoPagina
from app.paquetes.seguridad.casos_uso import (
    cu01_iniciar_sesion as cu01,
    cu02_gestionar_usuarios as cu02,
    cu03_gestionar_roles_permisos as cu03,
    cu04_consultar_bitacora as cu04,
)
from app.paquetes.seguridad.schemas import (
    AsignarRolEntrada, BitacoraSalida, CambiarContrasenaEntrada, ContrasenaTemporalSalida, IniciarSesionEntrada,
    OpcionesBitacoraSalida, PerfilSalida, PermisoSalida, PersonaSinCuentaSalida, RecuperarContrasenaEntrada,
    RestablecerContrasenaEntrada, ResumenInicioSalida, RolActualizar, RolSalida, SesionSalida,
    SolicitudRecuperacionSalida, UsuarioActualizar, UsuarioCrear, UsuarioSalida, ValidarTokenSalida,
)

router = APIRouter(prefix="/seguridad", tags=["seguridad"])


# ---- CU01: iniciar sesión, bloqueos y recuperación de contraseña ------------
@router.post("/sesion", response_model=SesionSalida, summary="CU01 - Iniciar sesión")
async def iniciar_sesion(datos: IniciarSesionEntrada, sesion: Sesion, request: Request):
    ip_cliente = request.client.host if request.client else None
    return await cu01.iniciar_sesion(sesion, datos, ip_cliente)


@router.get("/perfil", response_model=PerfilSalida, summary="CU01 - Datos del usuario conectado")
async def perfil(usuario: Usuario, sesion: Sesion):
    return await cu01.obtener_perfil(sesion, usuario.id_usuario)


@router.post("/perfil/contrasena", response_model=Mensaje, summary="CU01 - Cambiar mi contraseña")
async def cambiar_contrasena(datos: CambiarContrasenaEntrada, usuario: Usuario, sesion: Sesion):
    await cu01.cambiar_contrasena(sesion, usuario, datos)
    return Mensaje(mensaje="Contraseña actualizada.")


@router.post("/recuperar-contrasena", response_model=Mensaje, summary="CU01 - Solicitar recuperación por correo")
async def recuperar_contrasena(datos: RecuperarContrasenaEntrada, sesion: Sesion, request: Request):
    ip_cliente = request.client.host if request.client else None
    return Mensaje(mensaje=await cu01.solicitar_recuperacion(sesion, datos.dato, ip_cliente))


@router.get("/recuperar-contrasena/validar", response_model=ValidarTokenSalida, summary="CU01 - Validar token de recuperación")
async def validar_token(token: str, sesion: Sesion):
    return await cu01.validar_token_recuperacion(sesion, token)


@router.post("/restablecer-contrasena", response_model=Mensaje, summary="CU01 - Restablecer contraseña con token")
async def restablecer_contrasena(datos: RestablecerContrasenaEntrada, sesion: Sesion, request: Request):
    ip_cliente = request.client.host if request.client else None
    mensaje = await cu01.restablecer_contrasena_con_token(sesion, datos, ip_cliente)
    return Mensaje(mensaje=mensaje)


@router.get("/inicio", response_model=ResumenInicioSalida, summary="CU01 - Panel de inicio")
async def inicio(usuario: Usuario, sesion: Sesion):
    return await cu01.resumen_inicio(sesion, usuario)


# ---- CU02: gestionar usuarios ---------------------------------------------------
@router.get("/usuarios", response_model=Pagina[UsuarioSalida], summary="CU02 - Listar usuarios")
async def listar_usuarios(
    _: Administrador, sesion: Sesion,
    q: str | None = None, id_rol: int | None = None,
    estado: Literal["activo", "inactivo", "bloqueado"] | None = None,
    pagina: NumeroPagina = 1, tamano: TamanoPagina = 10,
):
    return await cu02.listar(sesion, q, id_rol, estado, pagina, tamano)


@router.get("/usuarios/personas-sin-cuenta", response_model=list[PersonaSinCuentaSalida],
            summary="CU02 - Personas que pueden recibir una cuenta con el rol indicado")
async def personas_sin_cuenta(_: Administrador, sesion: Sesion, id_rol: int, q: str | None = None):
    return await cu02.personas_sin_cuenta(sesion, id_rol, q)


@router.get("/usuarios/solicitudes-recuperacion", response_model=list[SolicitudRecuperacionSalida],
            summary="CU02 - Solicitudes de recuperación de contraseña pendientes")
async def solicitudes_recuperacion(_: Administrador, sesion: Sesion):
    return await cu02.solicitudes_recuperacion(sesion)


@router.get("/usuarios/{id_usuario}", response_model=UsuarioSalida, summary="CU02 - Ver usuario")
async def obtener_usuario(id_usuario: int, _: Administrador, sesion: Sesion):
    return await cu02.obtener(sesion, id_usuario)


@router.post("/usuarios", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED,
             summary="CU02 - Crear usuario")
async def crear_usuario(datos: UsuarioCrear, _: Administrador, sesion: Sesion):
    return await cu02.crear(sesion, datos)


@router.patch("/usuarios/{id_usuario}", response_model=UsuarioSalida, summary="CU02 - Modificar usuario")
async def actualizar_usuario(id_usuario: int, datos: UsuarioActualizar, admin: Administrador, sesion: Sesion):
    return await cu02.actualizar(sesion, admin, id_usuario, datos)


@router.delete("/usuarios/{id_usuario}", response_model=UsuarioSalida,
               summary="CU02 - Desactivar usuario (no se borra)")
async def desactivar_usuario(id_usuario: int, admin: Administrador, sesion: Sesion):
    return await cu02.desactivar(sesion, admin, id_usuario)


@router.post("/usuarios/{id_usuario}/restablecer-contrasena", response_model=ContrasenaTemporalSalida,
             summary="CU02 - Restablecer contraseña (contraseña temporal)")
async def restablecer_contrasena(id_usuario: int, _: Administrador, sesion: Sesion):
    return await cu02.restablecer_contrasena(sesion, id_usuario)


# ---- CU03: roles y permisos -------------------------------------------------------
@router.get("/roles", response_model=list[RolSalida], summary="CU03 - Listar roles")
async def listar_roles(_: Administrador, sesion: Sesion):
    return await cu03.listar_roles(sesion)


@router.patch("/roles/{id_rol}", response_model=RolSalida, summary="CU03 - Editar descripción del rol")
async def actualizar_rol(id_rol: int, datos: RolActualizar, _: Administrador, sesion: Sesion):
    return await cu03.actualizar_descripcion(sesion, id_rol, datos.descripcion_rol)


@router.get("/permisos", response_model=list[PermisoSalida], summary="CU03 - Matriz de permisos por rol")
async def permisos(_: Administrador):
    return cu03.matriz_permisos()


@router.patch("/usuarios/{id_usuario}/rol", response_model=UsuarioSalida, summary="CU03 - Asignar rol a un usuario")
async def asignar_rol(id_usuario: int, datos: AsignarRolEntrada, admin: Administrador, sesion: Sesion):
    await cu03.asignar_rol(sesion, admin, id_usuario, datos.id_rol)
    return await cu02.obtener(sesion, id_usuario)


# ---- CU04: bitácora -----------------------------------------------------------------
@router.get("/bitacora", response_model=Pagina[BitacoraSalida], summary="CU04 - Consultar bitácora")
async def listar_bitacora(
    _: Administrador, sesion: Sesion,
    desde: date | None = None, hasta: date | None = None,
    modulo: str | None = None, tabla: str | None = None, operacion: str | None = None,
    usuario: str | None = None, texto: Annotated[str | None, Query(max_length=100)] = None,
    pagina: NumeroPagina = 1, tamano: TamanoPagina = 20,
):
    return await cu04.listar(sesion, desde=desde, hasta=hasta, modulo=modulo, tabla=tabla,
                             operacion=operacion, usuario=usuario, texto=texto, pagina=pagina, tamano=tamano)


@router.get("/bitacora/opciones", response_model=OpcionesBitacoraSalida, summary="CU04 - Valores para los filtros")
async def opciones_bitacora(_: Administrador, sesion: Sesion):
    return await cu04.opciones(sesion)
