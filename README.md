# ThermalGuard DSS

A web-based Decision Support System that helps prevent heat-related injuries for outdoor workers. It pulls real-time weather data, calculates the Wet Bulb Globe Temperature (WBGT), and tells you whether it's safe to work outside based on OSHA/NIOSH safety standards.

## How It Works

1. The user searches for any city in the world using the OpenWeatherMap API.
2. The app fetches the current temperature, humidity, and wind speed.
3. It runs these values through the **Stull regression formula** to calculate the Wet Bulb Temperature:

```
Tw = T * atan(0.151977 * sqrt(RH + 8.313659))
     + atan(T + RH)
     - atan(RH - 1.676331)
     + 0.00391838 * RH^1.5 * atan(0.023101 * RH)
     - 4.686035
```

4. If the worker is wearing heavy PPE, a **+5°C penalty** is added (since protective gear traps heat).
5. The adjusted value is compared against OSHA/NIOSH threshold tables to classify risk:

   **Acclimatized Workers (>14 days on site):**

   | Risk Level | WBGT Range (°C) |
   |------------|-----------------|
   | Safe | Below 25 |
   | Caution | 25 – 28 |
   | Warning | 28 – 31 |
   | Danger | 31 – 34 |
   | Extreme Danger | Above 34 |

   **Unacclimatized Workers:**

   | Risk Level | WBGT Range (°C) |
   |------------|-----------------|
   | Safe | Below 22 |
   | Caution | 22 – 25 |
   | Warning | 25 – 28 |
   | Danger | 28 – 31 |
   | Extreme Danger | Above 31 |

   These thresholds shift further down for heavier activity levels (moderate: -2°C, heavy: -4°C).

6. A 24-hour forecast chart shows projected WBGT so managers can plan shifts around safe windows.

## Tech Stack

- **Python** — core language
- **Streamlit** — web framework
- **Plotly** — interactive charts (gauge + forecast)
- **OpenWeatherMap API** — live weather data
