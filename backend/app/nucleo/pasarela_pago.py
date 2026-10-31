"""
Pasarela de pago en línea: Stripe Checkout en MODO DE PRUEBA (tarjetas de prueba, sin dinero real).

- crear_sesion_pago(): crea una "sesión de pago" en Stripe y devuelve la página de pago a la que
  se redirige al tutor o estudiante.
- obtener_sesion(): consulta a Stripe el estado de una sesión. El backend NUNCA confía en lo que
  dice el navegador: el pago se da por hecho solo si Stripe responde que la sesión está pagada.

Se usa la API REST de Stripe con urllib (como el envío por Brevo en correo.py): no requiere
instalar el paquete "stripe". La clave secreta va en STRIPE_SECRET_KEY (.env o variables del
servidor), nunca en el repositorio; solo se aceptan claves de prueba (sk_test_...).
"""
import asyncio
import base64
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from app.nucleo.config import obtener_config
from app.nucleo.errores import ErrorNegocio

logger = logging.getLogger("app.pasarela_pago")

URL_STRIPE = "https://api.stripe.com/v1"


def habilitada() -> bool:
    """El pago en línea solo se ofrece con una clave de PRUEBA configurada."""
    return obtener_config().STRIPE_SECRET_KEY.startswith("sk_test_")


def _llamar_sincrono(metodo: str, ruta: str, datos: dict | None = None) -> dict:
    cfg = obtener_config()
    if not habilitada():
        raise ErrorNegocio("El pago en línea no está habilitado.", "pago_en_linea_deshabilitado")
    credencial = base64.b64encode(f"{cfg.STRIPE_SECRET_KEY}:".encode()).decode()
    cuerpo = urllib.parse.urlencode(datos or {}).encode() if datos is not None else None
    peticion = urllib.request.Request(
        f"{URL_STRIPE}{ruta}", data=cuerpo, method=metodo,
        headers={"Authorization": f"Basic {credencial}", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=20) as respuesta:
            return json.loads(respuesta.read())
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", "ignore")[:300]
        logger.error("Stripe respondió %s: %s", exc.code, detalle)
        raise ErrorNegocio("La pasarela de pago rechazó la operación. Intente más tarde.", "error_pasarela") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.error("No se pudo conectar con Stripe: %s", exc)
        raise ErrorNegocio("No se pudo conectar con la pasarela de pago. Intente más tarde.", "error_pasarela") from exc


async def crear_sesion_pago(monto_centavos: int, descripcion: str, referencia: dict, url_exito: str,
                            url_cancelar: str) -> dict:
    """Sesión de Stripe Checkout para un solo cobro. Devuelve {'id': 'cs_test_...', 'url': 'https://checkout...'}."""
    datos = {
        "mode": "payment",
        "success_url": url_exito,
        "cancel_url": url_cancelar,
        "line_items[0][quantity]": 1,
        "line_items[0][price_data][currency]": obtener_config().STRIPE_MONEDA,
        "line_items[0][price_data][unit_amount]": monto_centavos,
        "line_items[0][price_data][product_data][name]": descripcion,
        **{f"metadata[{k}]": v for k, v in referencia.items()},
    }
    sesion = await asyncio.to_thread(_llamar_sincrono, "POST", "/checkout/sessions", datos)
    return {"id": sesion["id"], "url": sesion["url"]}


async def obtener_sesion(id_sesion: str) -> dict:
    """Estado de la sesión según Stripe: payment_status ('paid' = pagado), amount_total, currency y metadata."""
    sesion = await asyncio.to_thread(_llamar_sincrono, "GET", f"/checkout/sessions/{urllib.parse.quote(id_sesion)}")
    return {
        "id": sesion["id"],
        "pagado": sesion.get("payment_status") == "paid",
        "monto_centavos": sesion.get("amount_total"),
        "moneda": sesion.get("currency"),
        "referencia": sesion.get("metadata") or {},
    }
