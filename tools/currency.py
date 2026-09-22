from infrastructure.api_client import LightweightAPIClient


class CurrencyTool:
    """
    Herramienta para consultar tipos de cambio
    y realizar conversiones.

    El IntentParser se encarga de interpretar
    el lenguaje natural y extraer:

        amount
        from_currency
        to_currency

    Esta herramienta únicamente recibe esos
    datos estructurados y consulta la API.
    """

    def __init__(self, api_client=None):

        self.api_client = (
            api_client
            or LightweightAPIClient()
        )

    # ==========================================================
    # EJECUTAR CONVERSIÓN
    # ==========================================================

    def execute(
        self,
        amount: float = 1.0,
        from_currency: str = "USD",
        to_currency: str = "PEN"
    ) -> str:
        """
        Ejecuta una conversión utilizando
        datos previamente interpretados.

        Ejemplo:

            amount = 35
            from_currency = USD
            to_currency = PEN
        """

        # ======================================================
        # NORMALIZAR DATOS
        # ======================================================

        try:

            amount = float(amount)

        except (
            TypeError,
            ValueError
        ):

            amount = 1.0

        from_currency = (
            str(from_currency)
            .upper()
            .strip()
        )

        to_currency = (
            str(to_currency)
            .upper()
            .strip()
        )

        # ======================================================
        # CONSULTAR TIPO DE CAMBIO
        # ======================================================

        rate = self.api_client.get_exchange_rate(
            from_currency,
            to_currency
        )

        if rate is None:

            return (
                f"No pude obtener el tipo de cambio "
                f"{from_currency}/{to_currency} "
                "en este momento."
            )

        # ======================================================
        # CALCULAR CONVERSIÓN
        # ======================================================

        converted = amount * rate

        # ======================================================
        # RESPUESTA PARA 1 UNIDAD
        # ======================================================

        if amount == 1:

            return (
                f"El tipo de cambio de referencia es "
                f"1 {from_currency} ≈ "
                f"{rate:.2f} {to_currency}."
            )

        # ======================================================
        # RESPUESTA PARA CANTIDADES
        # ======================================================

        return (
            f"{amount:g} {from_currency} ≈ "
            f"{converted:.2f} {to_currency} "
            f"(tipo de cambio de referencia: "
            f"{rate:.2f})."
        )
