import pandas as pd
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Modelo de entrada para validación
class PowerPlant(BaseModel):
    name: str
    type: str
    efficiency: float
    pmin: float
    pmax: float

class Payload(BaseModel):
    load: float
    fuels: Dict[str, float]
    powerplants: List[PowerPlant]

# Función utilitaria para truncar valores decimales sin redondear
def truncate(x, decimals=1):
    factor = 10 ** decimals
    return int(x * factor) / factor

# Lógica principal de cálculo
def calculate_production(data):
    load = data['load']
    co2_price = data['fuels']['co2(euro/ton)']
    wind_percent = data['fuels']['wind(%)'] / 100

    fuels = pd.DataFrame(list(data['fuels'].items()), columns=['fuel', 'price'])
    fuels.loc[fuels['fuel'] == 'wind(%)', 'price'] = 0

    powerplants = pd.DataFrame(data['powerplants'])
    fuel_relation = {
        'gasfired': 'gas(euro/MWh)',
        'turbojet': 'kerosine(euro/MWh)',
        'windturbine': 'wind(%)'
    }
    powerplants['fuel'] = powerplants['type'].map(fuel_relation)
    powerplants = powerplants.merge(fuels, on='fuel', how='left')
    powerplants.loc[powerplants['type'] == 'windturbine', 'pmax'] *= wind_percent
    powerplants['pmax'] = powerplants['pmax'].apply(truncate)
    powerplants['pmin'] = powerplants['pmin'].apply(truncate)

    emission_map = {
        'gasfired': 0.3,
        'turbojet': 0.3,
        'windturbine': 0.0
    }
    powerplants['co2_emission_factor'] = powerplants['type'].map(emission_map)
    powerplants['marginal_cost'] = (
        powerplants['price'] / powerplants['efficiency'] +
        powerplants['co2_emission_factor'] * co2_price
    )

    powerplants = powerplants.sort_values(by='marginal_cost').reset_index(drop=True)
    powerplants['cumsum_pmax'] = powerplants['pmax'].cumsum()
    powerplants['next_pmin'] = powerplants['pmin'].shift(-1).fillna(0)
    powerplants['next_pmin'] = powerplants['next_pmin'].apply(truncate)
    powerplants['p'] = powerplants.apply(
        lambda row: min(row['pmax'], max(0, load - (row['cumsum_pmax'] - row['pmax']))),
        axis=1
    )
    powerplants['p'] = powerplants['p'].apply(truncate)

    # Ajuste condicional para garantizar que si el remanente < pmin siguiente, se reserva y se corrige
    for i in range(len(powerplants) - 1):
        remainder = load - powerplants.loc[i, 'cumsum_pmax']
        next_pmin = powerplants.loc[i, 'next_pmin']
        if 0 < remainder < next_pmin:
            deficit = next_pmin - remainder
            if powerplants.loc[i, 'p'] > deficit:
                powerplants.loc[i, 'p'] -= deficit
                powerplants.loc[i + 1, 'p'] = next_pmin

    return powerplants[['name', 'p']].to_dict(orient='records')

# Endpoint requerido por el challenge
@app.post("/productionplan")
async def production_plan(payload: Payload):
    try:
        data = json.loads(payload.json())
        result = calculate_production(data)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in production plan calculation: {str(e)}")
