"""
common.py -- shared constants, unit conversions, atmosphere, and rule limits for the
SAE Aero Design 2027 Regular Class conceptual sizing (analysis/sizing/).

Units: the sizing work is done in US units (ft, lbf, slug, s) because the rules and TDS are
in English units. Propulsion internals use SI (see propulsion.py) and convert at the boundary.

Tags used in comments:
  [VERIFIED]   read from a source file (document ID + line given)
  [INFERRED]   engineering reasoning
  [UNVERIFIED] assumption that still needs checking (test, measurement, or source)
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RAW = os.path.join(ROOT, "reference", "raw")
DATA = os.path.join(ROOT, "reference", "data")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- units
G = 32.174              # ft/s^2
FT_PER_M = 3.28084
N_PER_LBF = 4.44822
IN_PER_FT = 12.0
FPS_PER_MPH = 5280.0 / 3600.0
KG_PER_SLUGFT3 = 515.379  # (kg/m^3) per (slug/ft^3)

# ---------------------------------------------------------------- rules (rules_2027)
SPAN_MIN_IN = 72.0      # "greater than 72 in" [VERIFIED rules_2027 line 1548]
SPAN_MAX_IN = 96.0      # "less than 96 in"    [VERIFIED rules_2027 line 1550]
CHORD_MIN_IN = 4.0      # "greater than 4 in"  [VERIFIED rules_2027 line 1551]
LENGTH_MAX_IN = 120.0   # body axis length < 120 in [VERIFIED rules_2027 line 1552-1553]
GROSS_MAX_LB = 55.0     # gross takeoff weight <= 55 lb [VERIFIED rules_2027 line 715]
TO_DIST_FT = 100.0      # airborne within 100 ft [VERIFIED rules_2027 line 1015]
TURN_AFTER_FT = 400.0   # no turn before 400 ft [VERIFIED rules_2027 line 1015]
LAND_DIST_FT = 400.0    # land within 400 ft [VERIFIED rules_2027 line 1049]
BATT_MAH = 2200.0       # 4S LiPo, max 2200 mAh [VERIFIED rules_2027 line 1574-1575]
BATT_CELLS = 4
# Prop limit: 12 in per motor (2 motors) or 9 in per motor (4 motors) [VERIFIED rules_2027 line 1577-1578];
# the limit is the SUM of prop diameters on one motor [VERIFIED faq_395 line 36].
# Since disk area ~ sum(D_i^2) is maximised by a single prop for a fixed sum(D_i), one prop per motor.

# Design margins on rule limits [INFERRED]: stay clear of the "<" limits by measurement tolerance.
SPAN_DESIGN_MAX_IN = 95.0
SPAN_DESIGN_MIN_IN = 73.0

# ---------------------------------------------------------------- payload (team working assumptions)
W_FILLED = 4.05         # lb gross, filled bottle target (>= 4.0 lb rule) [VERIFIED rules_2027 line 1592-1595; the 0.05 lb margin is a team choice]
W_EMPTY = 1.05          # lb gross, empty bottle target (> 1.0 lb rule)
SLOT_DIA_IN = 4.7       # bottle slot envelope, until real bottles are measured [UNVERIFIED]
SLOT_LEN_IN = 13.0
PTS_EMPTY = 3.0         # FS = 3*EB + 11*FB [VERIFIED rules_2027 line 1632]
PTS_FILLED = 11.0

# ---------------------------------------------------------------- site
KLAL_ELEV_FT = 141.8    # [VERIFIED klal_airnav, PROJECT_MEMORY]

# ---------------------------------------------------------------- atmosphere
RHO_SL = 0.0023769      # slug/ft^3, ISA sea level


def rho_from_da(da_ft):
    """ISA density (slug/ft^3) at a given density altitude (ft). Troposphere model."""
    da_ft = np.asarray(da_ft, dtype=float)
    return RHO_SL * (1.0 - 6.87559e-6 * da_ft) ** 4.25588


def da_from_rho(rho):
    rho = np.asarray(rho, dtype=float)
    return (1.0 - (rho / RHO_SL) ** (1.0 / 4.25588)) / 6.87559e-6


# Dynamic viscosity of air: Sutherland. For Re estimates use a typical March afternoon, 80 F.
def mu_air(T_F=80.0):
    """Dynamic viscosity, slug/(ft s)."""
    T = (T_F - 32.0) / 1.8 + 273.15
    mu_si = 1.716e-5 * (T / 273.15) ** 1.5 * (273.15 + 110.4) / (T + 110.4)  # Pa s
    return mu_si * 0.0208854  # Pa s -> slug/(ft s)


def reynolds(V_fps, chord_ft, rho, T_F=80.0):
    return rho * V_fps * chord_ft / mu_air(T_F)


def save_csv(df, name):
    path = os.path.join(OUT, name)
    df.to_csv(path, index=False, float_format="%.5g")
    return path
