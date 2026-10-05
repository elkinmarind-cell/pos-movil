"""Todo el dinero del sistema pasa por aqui: Decimal y un unico redondeo."""
from decimal import Decimal, ROUND_HALF_UP

CENTAVO = Decimal("0.01")


def dinero(valor) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)
