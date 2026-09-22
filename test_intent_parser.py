from core.intent_parser import IntentParser


parser = IntentParser()


pruebas = [
    "que hora es",
    "que hora es en lima",
    "dime la hora de mexico",
    "dime la hora de la india",
    "que hora es en nueva york",
    "dime el clima de lima",
    "dime el clima de mexico",
    "dime el clima de new york",
    "que clima hace en madrid",
    "cuanto son 35 dolares en soles",
    "cuanto es 40 soles a dolares",
]


for pregunta in pruebas:
    print("\nPREGUNTA:", pregunta)
    print("RESULTADO:", parser.parse(pregunta))
