"""Verifica que cada esquema de salida solo pida campos que el modelo ORM puede dar."""
import sys

from app import models, schemas

MAPA = {
    "UsuarioOut": models.Usuario, "RolOut": models.Rol, "PermisoOut": models.Permiso,
    "CategoriaOut": models.Categoria, "MarcaOut": models.Marca, "ProductoOut": models.Producto,
    "EquipoOut": models.EquipoImei, "MovimientoOut": models.MovimientoInventario,
    "ClienteOut": models.Cliente, "OrdenCompraOut": models.OrdenCompra,
    "OrdenCompraDetalleOut": models.OrdenCompraDetalle, "TurnoOut": models.TurnoCaja,
    "VentaOut": models.Venta, "VentaDetalleOut": models.VentaDetalle, "PagoOut": models.Pago,
    "ApartadoOut": models.Apartado, "GarantiaOut": models.Garantia,
    "DevolucionOut": models.Devolucion, "OrdenServicioOut": models.OrdenServicio,
    "OperadorOut": models.Operador, "PlanOut": models.Plan, "ActivacionOut": models.ActivacionLinea,
    "DispositivoOut": models.DispositivoIot, "EventoOut": models.EventoIot, "AlertaOut": models.Alerta,
}
CALCULADOS = {"disponibles", "dias_restantes"}

fallos = []
for nombre, modelo in MAPA.items():
    esquema = getattr(schemas, nombre)
    atributos = set(modelo.__mapper__.columns.keys()) | set(modelo.__mapper__.relationships.keys())
    for campo in esquema.model_fields:
        if campo not in atributos and campo not in CALCULADOS:
            fallos.append(f"{nombre}.{campo} no existe en {modelo.__name__}")

print(f"esquemas verificados: {len(MAPA)}")
if fallos:
    print(f"{len(fallos)} campos sin respaldo en el modelo:")
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("Todos los esquemas de salida coinciden con el modelo ORM.")
