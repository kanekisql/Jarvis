import re
import unicodedata
from typing import Optional, Dict, Any


class IntentParser:
    """
    Analizador central de intenciones de JARVIS.

    Su función es transformar lenguaje natural en
    información estructurada que posteriormente
    utilizarán las herramientas.

    El parser NO consulta APIs.
    Solo interpreta la solicitud.

    Ejemplos:

        "dime la hora de Nueva York"

        {
            "intent": "time",
            "location": "Nueva York"
        }

        "que clima hace Madrid"

        {
            "intent": "weather",
            "location": "Madrid"
        }

        "cuanto son 35 dolares en soles"

        {
            "intent": "currency",
            "amount": 35.0,
            "from_currency": "USD",
            "to_currency": "PEN"
        }
    """

    def __init__(self):

        # ======================================================
        # PALABRAS CLAVE: HORA
        # ======================================================

        self.time_keywords = {
            "hora",
            "horas",
            "horario",
            "tiempo",
        }

        # ======================================================
        # PALABRAS CLAVE: CLIMA
        # ======================================================

        self.weather_keywords = {
            "clima",
            "temperatura",
            "temperaturas",
            "meteorologia",
            "meteorología",
            "tiempo",
            "frio",
            "frío",
            "calor",
            "llueve",
            "lluvia",
            "lloviendo",
            "nublado",
            "nubes",
            "viento",
        }

        # ======================================================
        # PALABRAS CLAVE: MONEDA
        # ======================================================

        self.currency_keywords = {
            "dolar",
            "dólar",
            "dolares",
            "dólares",
            "usd",
            "euro",
            "euros",
            "eur",
            "yen",
            "yenes",
            "jpy",
            "peso",
            "pesos",
            "mxn",
            "sol",
            "soles",
            "pen",
            "moneda",
            "cambio",
            "convertir",
            "convierte",
            "conversion",
            "conversión",
        }

        # ======================================================
        # PALABRAS CLAVE: BÚSQUEDA DE CÓDIGO
        # ======================================================

        self.code_search_keywords = {
            "busca",
            "buscar",
            "buscame",
            "búscame",
            "donde esta",
            "dónde está",
            "donde se usa",
            "dónde se usa",
        }

    # ==========================================================
    # NORMALIZACIÓN
    # ==========================================================

    def normalize(
        self,
        text: str
    ) -> str:
        """
        Normaliza el texto para facilitar
        la detección de intenciones y parámetros.

        Ejemplo:

            "¿Qué hora es en Lima?"

        se convierte en:

            "que hora es en lima"
        """

        text = text.lower().strip()

        text = unicodedata.normalize(
            "NFD",
            text
        )

        text = "".join(
            char
            for char in text
            if unicodedata.category(char) != "Mn"
        )

        text = re.sub(
            r"[¿?!¡]+",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text

    # ==========================================================
    # DETECCIÓN DE INTENCIÓN
    # ==========================================================

    def detect_intent(
        self,
        text: str
    ) -> Optional[str]:
        """
        Determina la intención principal.

        Prioridad:

            TIME
            WEATHER
            CURRENCY
            GENERAL
        """

        normalized = self.normalize(text)

        if self._contains_time_intent(
            normalized
        ):
            return "time"

        if self._contains_weather_intent(
            normalized
        ):
            return "weather"

        if self._contains_currency_intent(
            normalized
        ):
            return "currency"
        
        if self._contains_code_search_intent(
            normalized
        ):
            return "code_search"

        return "general"

    # ==========================================================
    # DETECCIÓN DE HORA
    # ==========================================================

    def _contains_time_intent(
        self,
        normalized: str
    ) -> bool:

        if re.search(
            r"\bhora\b",
            normalized
        ):
            return True

        if re.search(
            r"\bhorario\b",
            normalized
        ):
            return True

        return False

    # ==========================================================
    # DETECCIÓN DE CLIMA
    # ==========================================================

    def _contains_weather_intent(
        self,
        normalized: str
    ) -> bool:

        for keyword in self.weather_keywords:

            if re.search(
                rf"\b{re.escape(keyword)}\b",
                normalized
            ):
                return True

        return False

    # ==========================================================
    # DETECCIÓN DE MONEDA
    # ==========================================================

    def _contains_currency_intent(
        self,
        normalized: str
    ) -> bool:

        for keyword in self.currency_keywords:

            if re.search(
                rf"\b{re.escape(keyword)}\b",
                normalized
            ):
                return True

        return False

    # ==========================================================
    # DETECCIÓN DE BÚSQUEDA DE CÓDIGO
    # ==========================================================

    def _contains_code_search_intent(
        self,
        normalized: str
    ) -> bool:

        for keyword in self.code_search_keywords:

            if re.search(
                rf"\b{re.escape(keyword)}\b",
                normalized
            ):
                return True

        return False    

    # ==========================================================
    # EXTRACCIÓN DE UBICACIÓN
    # ==========================================================

            
    def extract_location(
        self,
        text: str
    ) -> Optional[str]:
        """
        Extrae la ubicación indicada por el usuario.

        Usa el texto normalizado para detectar el patrón,
        pero conserva el texto original para no perder
        tildes ni caracteres especiales de la ubicación.
        """

        normalized = self.normalize(text)

        # ======================================================
        # FUNCIÓN INTERNA PARA RECUPERAR EL TEXTO ORIGINAL
        # ======================================================

        def get_original_location(
            normalized_location: str
        ) -> str:

            words = normalized_location.split()

            if not words:
                return ""

            # Buscar las palabras normalizadas dentro
            # del texto original conservando las tildes.
            original_words = text.split()

            for i in range(
                len(original_words) - len(words) + 1
            ):

                candidate = " ".join(
                    original_words[
                        i:i + len(words)
                    ]
                )

                if self.normalize(candidate) == normalized_location:
                    return candidate

            return normalized_location

        # ======================================================
        # 1. PATRONES CON PREPOSICIÓN
        # ======================================================

        explicit_patterns = [

            r"\ben\s+(.+)$",

            r"\bde\s+la\s+(.+)$",

            r"\bde\s+el\s+(.+)$",

            r"\bde\s+(.+)$",

            r"\bpara\s+(.+)$",
        ]

        for pattern in explicit_patterns:

            match = re.search(
                pattern,
                normalized,
                re.IGNORECASE
            )

            if match:

                normalized_location = match.group(
                    1
                ).strip()

                location = get_original_location(
                    normalized_location
                )

                location = self._clean_location(
                    location
                )

                if location:
                    return location

        # ======================================================
        # 2. PATRONES NATURALES
        # ======================================================

        natural_patterns = [

            # "que clima hace Madrid"
            r"^(?:que|qué)\s+clima\s+"
            r"(?:hace\s+)?(.+)$",

            # "como esta el clima Madrid"
            r"^(?:como|cómo)\s+"
            r"(?:esta|está)\s+"
            r"(?:el\s+)?clima\s+(.+)$",

            # "temperatura Madrid"
            r"^(?:dime\s+)?"
            r"(?:la\s+)?temperatura\s+(.+)$",

            # "hora Nueva York"
            r"^(?:dime\s+)?"
            r"(?:la\s+)?hora\s+(.+)$",

            # "clima Mexico"
            r"^clima\s+(.+)$",
        ]

        for pattern in natural_patterns:

            match = re.search(
                pattern,
                normalized,
                re.IGNORECASE
            )

            if match:

                normalized_location = match.group(
                    1
                ).strip()

                location = get_original_location(
                    normalized_location
                )

                location = self._clean_location(
                    location
                )

                if location:
                    return location

        return None


    # ==========================================================
    # LIMPIEZA DE UBICACIÓN
    # ==========================================================

    def _clean_location(
        self,
        location: str
    ) -> str:
        """
        Limpia palabras y signos que no pertenecen
        a la ubicación.
        """

        location = location.strip()

        # ======================================================
        # ELIMINAR SIGNOS
        # ======================================================

        location = re.sub(
            r"[¿?!¡.,;:]+",
            " ",
            location
        )

        # ======================================================
        # FRASES QUE NO PERTENECEN A LA UBICACIÓN
        # ======================================================

        stop_patterns = [

            r"\bahora mismo\b",

            r"\ben este momento\b",

            r"\bactualmente\b",

            r"\bactual\b",

            r"\bactuales\b",

            r"\bexacta\b",

            r"\bexacto\b",

            r"\bpor favor\b",

            r"\bdime\b",

            r"\bme dices\b",

            r"\bme puedes decir\b",

            r"\bpuedes decirme\b",

            r"\bpuedes decir\b",
        ]

        for pattern in stop_patterns:

            location = re.sub(
                pattern,
                " ",
                location,
                flags=re.IGNORECASE
            )

        # ======================================================
        # ARTÍCULOS INICIALES
        # ======================================================

        location = re.sub(
            r"^(la|el|las|los)\s+",
            "",
            location,
            flags=re.IGNORECASE
        )

        # ======================================================
        # LIMPIAR ESPACIOS
        # ======================================================

        location = re.sub(
            r"\s+",
            " ",
            location
        ).strip()

        if not location:
            return ""

        # ======================================================
        # FORMATO DE PRESENTACIÓN
        # ======================================================

        return location.title()

    # ==========================================================
    # MONEDAS
    # ==========================================================

    def extract_currency(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Extrae:

            cantidad
            moneda origen
            moneda destino
        """

        normalized = self.normalize(
            text
        )

        currency_aliases = {

            "dolar": "USD",
            "dolares": "USD",
            "usd": "USD",

            "sol": "PEN",
            "soles": "PEN",
            "pen": "PEN",

            "euro": "EUR",
            "euros": "EUR",
            "eur": "EUR",

            "yen": "JPY",
            "yenes": "JPY",
            "jpy": "JPY",

            "peso": "MXN",
            "pesos": "MXN",
            "mxn": "MXN",
        }

        matches = []

        for alias, code in currency_aliases.items():

            for match in re.finditer(
                rf"\b{re.escape(alias)}\b",
                normalized
            ):

                matches.append(
                    (
                        match.start(),
                        code
                    )
                )

        matches.sort(
            key=lambda item: item[0]
        )

        currencies = [
            item[1]
            for item in matches
        ]

        amount = self._extract_amount(
            normalized
        )

        # ======================================================
        # DOS MONEDAS
        # ======================================================

        if len(currencies) >= 2:

            from_currency = currencies[0]

            to_currency = currencies[1]

        # ======================================================
        # UNA MONEDA
        # ======================================================

        elif len(currencies) == 1:

            from_currency = currencies[0]

            if from_currency == "USD":

                to_currency = "PEN"

            elif from_currency == "PEN":

                to_currency = "USD"

            else:

                to_currency = "PEN"

        # ======================================================
        # NINGUNA MONEDA
        # ======================================================

        else:

            from_currency = "USD"

            to_currency = "PEN"

        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
        }

    # ==========================================================
    # EXTRACCIÓN DE CANTIDAD
    # ==========================================================

    def _extract_amount(
        self,
        text: str
    ) -> float:
        """
        Extrae la primera cantidad numérica.

        Ejemplo:

            "35 dolares en soles"

        devuelve:

            35.0
        """

        match = re.search(
            r"\b(\d+(?:[.,]\d+)?)\b",
            text
        )

        if not match:
            return 1.0

        try:

            return float(
                match.group(1).replace(
                    ",",
                    "."
                )
            )

        except ValueError:

            return 1.0


    # ==========================================================
    # EXTRACCIÓN DE TÉRMINO DE BÚSQUEDA DE CÓDIGO
    # ==========================================================

    def extract_code_search_query(
        self,
        text: str
    ) -> Optional[str]:
        """
        Extrae exactamente qué desea buscar
        el usuario dentro del código.

        Conserva mayúsculas y minúsculas de los
        nombres del código.

        Ejemplos:

            "busca JarvisRouter"
                -> "JarvisRouter"

            "dónde está IntentParser"
                -> "IntentParser"

            "dónde se usa process_message"
                -> "process_message"
        """

        normalized = self.normalize(
            text
        )

        patterns = [

            r"^busca\s+(.+)$",

            r"^buscar\s+(.+)$",

            r"^buscame\s+(.+)$",

            r"^(?:donde|dónde)\s+esta\s+(.+)$",

            r"^(?:donde|dónde)\s+se\s+usa\s+(.+)$",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized,
                re.IGNORECASE
            )

            if match:

                normalized_query = (
                    match.group(1).strip()
                )

                # Buscar el mismo fragmento dentro
                # del texto original para conservar
                # mayúsculas y minúsculas.
                original_words = text.split()

                query_words = (
                    normalized_query.split()
                )

                for i in range(
                    len(original_words) - len(query_words) + 1
                ):

                    candidate = " ".join(
                        original_words[
                            i:i + len(query_words)
                        ]
                    )

                    if self.normalize(
                        candidate
                    ) == normalized_query:

                        candidate = re.sub(
                            r"[¿?!¡.,;:]+$",
                            "",
                            candidate
                        ).strip()

                        if candidate:
                            return candidate

                # Fallback
                if normalized_query:
                    return normalized_query

        return None

    # ==========================================================
    # PARSER COMPLETO
    # ==========================================================

    def parse(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Analiza completamente una consulta
        y devuelve información estructurada.
        """

        intent = self.detect_intent(
            text
        )

        result = {

            "intent": intent,

            "location": None,

            "amount": None,

            "from_currency": None,

            "to_currency": None,

            "query": None,

            "raw_text": text.strip(),
        }

        # ======================================================
        # HORA / CLIMA
        # ======================================================

        if intent in {
            "time",
            "weather"
        }:

            result["location"] = (
                self.extract_location(
                    text
                )
            )

        # ======================================================
        # MONEDA
        # ======================================================

        elif intent == "currency":

            currency_data = (
                self.extract_currency(
                    text
                )
            )

            result.update(
                currency_data
            )
            
        # ======================================================
        # BÚSQUEDA DE CÓDIGO
        # ======================================================

        elif intent == "code_search":

            result["query"] = (
                self.extract_code_search_query(
                    text
                )
            )


        return result
