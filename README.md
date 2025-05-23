# Powerplant Production Planner API

This project implements a solution to the "powerplant-coding-challenge" by building a REST API with FastAPI. The API computes an optimized energy production plan based on a given payload of fuel prices, load requirements, and plant specifications.

## 🚀 Endpoint

* **POST** `/productionplan`

  * Accepts a JSON payload with load, fuels, and powerplants.
  * Returns a JSON array of objects with `name` and `p` indicating the power to be produced by each plant.

## 🧠 Algorithm Overview

### Step-by-step Logic in `calculate_production()`

1. **Load input and normalize wind**

   * Extracts `load`, `co2_price`, and converts wind percentage to fraction.

2. **Build `fuels` and `powerplants` tables**

   * Merges fuel prices into powerplants.
   * Adjusts `pmax` for wind turbines based on wind availability.

3. **Truncate `pmax` and `pmin` to 0.1 MW**

   * Ensures values are compatible with dispatch precision.

4. **Assign CO2 emission factors and compute marginal cost**

   * Marginal cost = fuel cost per MWh / efficiency + 0.3 × CO2 €/ton (if applicable).

5. **Sort plants by increasing marginal cost (merit order)**

   * Most cost-efficient plants are prioritized.

6. **Precompute cumulative `pmax` and `next_pmin`**

   * Used to anticipate dispatch viability for the next plant.

7. **Initial power assignment with `apply()`**

   * Allocates production to each plant without exceeding load.

8. **Post-adjustment phase**

   * If remaining load is too small to meet `pmin` of the next plant,
     it adjusts current plant output and forces next plant to its `pmin`.

This two-pass logic ensures total load is met exactly, `pmin` is respected whenever possible, and merit-order is optimized.

## 🐳 Run with Docker

### 1. Create Dockerfile

```Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir fastapi uvicorn pandas
EXPOSE 8888
CMD ["uvicorn", "production_planner:app", "--host", "0.0.0.0", "--port", "8888"]
```

### 2. Build and run

```bash
docker build -t productionplanner .
docker run -p 8888:8888 productionplanner
```

### 3. Test the API

Open:

```
http://localhost:8888/docs
```

Use the Swagger UI to submit a POST request to `/productionplan` using any of the example payloads.

## 📄 Example input

```json
{
  "load": 480,
  "fuels": {
    "gas(euro/MWh)": 13.4,
    "kerosine(euro/MWh)": 50.8,
    "co2(euro/ton)": 20,
    "wind(%)": 60
  },
  "powerplants": [
    { "name": "windpark1", "type": "windturbine", "efficiency": 1, "pmin": 0, "pmax": 150 },
    { "name": "gasfiredbig1", "type": "gasfired", "efficiency": 0.53, "pmin": 100, "pmax": 460 }
  ]
}
```

## 📄 Example output

```json
[
  { "name": "windpark1", "p": 90 },
  { "name": "gasfiredbig1", "p": 390 }
]
```

## 👨‍💻 Author

Alexis Bolivar – implementation and functional logic by design.
