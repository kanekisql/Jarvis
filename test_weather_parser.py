from core.intent_parser import IntentParser
from tools.weather import WeatherTool


parser = IntentParser()
weather = WeatherTool()


preguntas = [
    "dime el clima de Lima",
    "dime el clima de Mexico",
    "dime el clima de New York",
    "que clima hace en Madrid",
    "que clima hace Madrid",
    "dime el clima de Lima",
    "dime el clima de Mexico",
    "dime el clima de New York",
    "que clima hace en Madrid",
    "que clima hace Madrid",
    "temperatura Madrid",
    "como esta el clima Lima",
    "clima Mexico",
    "que tiempo hace en New York",
    "temperatura de Madrid",
]


for pregunta in preguntas:

    datos = parser.parse(pregunta)

    print()
    print("PREGUNTA:", pregunta)
    print("PARSER:", datos)

    if datos["intent"] == "weather":

        respuesta = weather.execute(
            datos["location"]
        )

        print("JARVIS:", respuesta)

