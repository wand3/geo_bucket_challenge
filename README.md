# 🏠 Geo_bucket_challenge: Geospatial Property Engine

**Geo_bucket_challenge** is a high-performance backend API designed to solve the "Dirty Data" problem in real estate. Instead of relying on inconsistent user-inputted location names, it uses **Uber’s H3 Discrete Global Grid System** to "bucket" properties into precise hexagonal cells.


## 🚀 Key Features

* **H3 Hexagonal Bucketing:** Automatically snaps properties to a Resolution 8 grid ($\approx 0.74\text{ km}^2$) to ensure nearby listings are grouped together regardless of slight coordinate variances.
* **Intelligent Alias Mapping:** Learns location names (e.g., "Downtown" vs. "City Center") and maps them to the same spatial bucket.
* **K-Ring Search Expansion:** Uses hexagonal neighbor traversal to ensure users searching near cell borders don't miss out on properties just a few meters away.
* **Geocoding Fallback:** Integrates with OpenStreetMap (via Geopy) to translate text queries into coordinates when database aliases aren't found.

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| **Language** | **Python 3.10+** |
| **Framework** | **FastAPI** (Asynchronous, Type-safe) |
| **Database** | **PostgreSQL** with **PostGIS** for spatial data |
| **ORM** | **SQLModel** (Combining SQLAlchemy & Pydantic) |
| **Geospatial** | **Uber H3** (h3-py) & **GeoAlchemy2** |
| **Geocoding** | **Geopy** (Nominatim) |
| **Testing** | **Pytest** & **HTTPX** |

---

## 🧪 Testing Strategies

The project maintains a rigorous testing suite using `pytest` to ensure spatial accuracy and API reliability.

### 1. Unit Testing (Logic & Geospatial)
* **H3 Snapping:** Validating that coordinates within a specific radius correctly resolve to the same H3 Index.
* **K-Ring Logic:** Ensuring that searching a cell correctly pulls the 6 surrounding neighbors.
* **Data Models:** Validating Pydantic schemas for property creation and search.

### 2. Integration Testing (Database & API)
* **Transactional Isolation:** Every test runs in a `FORCE_ROLLBACK` session to keep the PostGIS database clean.
* **Spatial Queries:** Testing the `ILIKE` alias search and H3 bucket retrieval flow.

### 3. Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/
```

---

## 🗺️ How it Works: The 3-Step Search

1.  **Direct Alias Match:** The system checks if the search string (e.g., "Palm grove") exists in the `LocationAlias` table.
2.  **Geocoding Fallback:** If not found, it pings the Geocoding API to get a Lat/Lng.
3.  **Hexagonal Lookup:** The system converts those coordinates to an **H3 Index**, expands the search to the **K-Ring (1)** (neighboring hexagons), and returns all properties within those buckets.

---

## 📦 Installation

1.  **Clone the Repo:**
    ```bash
    git clone https://github.com/wand3/geo_bucket_challenge.git
    ```
2.  **Set Up Environment:**
    ```bash
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt

    touch .env
    # Ensure .env contains
      DATABASE_URL,
      DB_HOST,
      DB_PORT,
      DB_USER,
      DATABASE_NAME,
      DB_PASSWORD,
      SECRET_KEY,
      DATABASE_URL,
      TEST_DATABASE_URL,

    fastapi dev app/main.py

    ```

---
