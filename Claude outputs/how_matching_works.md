# Matching Architecture

> Sourced from `./Claude outputs/how_matching_works.mermaid`.

> For revisions, edit source diagram '*.mermaid' conanical file directly and copy here.

> The diagram shows how lunar reference data and Earth satellite data are
> normalized, compared, scored, ranked, and validated.

## Visual Key

| Visual | Meaning |
|---|---|
| 🔵 **Blue** | Moon reference data and lunar reference window |
| 🟢 **Green** | Earth candidate data, filtering, and candidate windows |
| 🟠 **Orange** | Shared feature extraction and similarity comparison |
| 🟣 **Purple** | Engineering purpose and adjustable mission weighting |
| 🟡 **Gold** | Weighted scoring, ranking, and final results |
| ⚪ **Gray** | Validation checks and known comparison limitations |
| `──>` **Normal line** | Supporting data or control input |
| `══>` **Heavy line** | Primary processing and scoring pipeline |

> **Reading convention:** Follow the heavy connectors to trace the primary
> matching pipeline. Normal connectors show supporting data and control inputs.

```mermaid
%%{init: {
  "theme": "base",
  "flowchart": {
    "curve": "basis",
    "nodeSpacing": 35,
    "rankSpacing": 55
  },
  "themeVariables": {
    "fontFamily": "Segoe UI, Arial, sans-serif",
    "fontSize": "15px",
    "lineColor": "#64748b",
    "primaryTextColor": "#172033"
  }
}}%%

flowchart TB

%% =========================================================
%% STAGE 1: SOURCE DATA
%% =========================================================

subgraph SOURCES["1. SOURCE DATA"]
direction LR

    subgraph MOON["MOON REFERENCE DATA"]
    direction TB
        M1["Elevation<br/>80 m laser altimeter"]
        M2["Average sunlight<br/>& permanent shadow"]
        M3["Surface temperature<br/>Diviner instrument"]
    end

    subgraph EARTH["EARTH CANDIDATE DATA"]
    direction TB
        E1["Elevation<br/>90 m Copernicus DEM"]
        E2["Vegetation index<br/>NASA MODIS"]
        E3["Land surface temperature<br/>NASA MODIS"]
        E4["Sun angle & darkness<br/>computed from latitude"]
    end

end

%% =========================================================
%% STAGE 2: PREPARATION
%% =========================================================

subgraph PREP["2. PREPARE COMPARABLE WINDOWS"]
direction LR

    MW["Lunar reference window<br/><b>10 km around selected spot</b>"]

    FILT["Filter Earth data<br/><b>bare, snow-free land</b><br/>399 map squares"]

    EW["Earth candidate windows<br/><b>10 km on common 80 m grid</b><br/>25,761 windows"]

end

%% =========================================================
%% STAGE 3: FEATURE COMPARISON
%% =========================================================

subgraph COMPARE["3. COMPARE THE SAME FEATURES"]
direction TB

    FP["Shared feature pipeline<br/><b>Same algorithm for Moon & Earth</b><br/>Slope • roughness • temperature • light"]

    FOM["Factor similarity<br/><b>Score each factor from 0 to 1</b><br/>NASA lunar simulant Figure of Merit"]

end

%% =========================================================
%% STAGE 4: PURPOSE AND SCORING
%% =========================================================

subgraph SCORE_STAGE["4. SCORE FOR THE MISSION PURPOSE"]
direction LR

    PUR["Engineering purpose<br/>Rover driving<br/>Shadow work<br/>Darkness survival"]

    W["Purpose-specific weights<br/><b>Team-set and adjustable</b>"]

    SCORE["Weighted Earth-window score<br/><b>Forest & farmland gated to zero</b>"]

end

%% =========================================================
%% STAGE 5: RANK AND VALIDATE
%% =========================================================

subgraph OUTPUT["5. RANK AND VALIDATE"]
direction TB

    RANK["Rank candidate windows<br/><b>Best window per map square</b>"]

    OUT["Ranked Earth sites<br/><b>Score reported per factor</b>"]

    subgraph VALIDATION["VALIDATION & LIMITS"]
    direction LR
        CHK["Validation checks<br/>Known NASA analog sites<br/>Forest & farmland controls"]

        LIM["Non-comparable factors<br/><b>Always shown as zero</b><br/>Gravity • vacuum • radiation"]
    end

end

%% =========================================================
%% DATA FLOW
%% =========================================================

M1 --> MW
M2 --> MW
M3 --> MW

E2 --> FILT
FILT --> EW
E1 --> EW

MW ==> FP
EW ==> FP

E3 --> FP
E4 --> FP

FP ==> FOM

PUR --> W
W ==> SCORE
FOM ==> SCORE

SCORE ==> RANK
RANK ==> OUT

OUT --> CHK
OUT --> LIM

%% =========================================================
%% VISUAL GRAMMAR
%% =========================================================

classDef moon fill:#E8F1FF,stroke:#2563EB,stroke-width:2px,color:#172033;
classDef earth fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#172033;
classDef compare fill:#FFF7ED,stroke:#EA580C,stroke-width:2px,color:#172033;
classDef purpose fill:#FAF5FF,stroke:#9333EA,stroke-width:2px,color:#172033;
classDef result fill:#FEFCE8,stroke:#CA8A04,stroke-width:2px,color:#172033;
classDef validation fill:#F1F5F9,stroke:#475569,stroke-width:1.5px,color:#172033;

class M1,M2,M3,MW moon;
class E1,E2,E3,E4,FILT,EW earth;
class FP,FOM compare;
class PUR,W purpose;
class SCORE,RANK,OUT result;
class CHK,LIM validation;

linkStyle default stroke:#64748B,stroke-width:2px;
```

## How to Read the Architecture

The matching process separates **reference data**, **candidate data**, **comparison logic**, and **mission-specific decision logic**.

1. **Moon reference data** defines the lunar environment being matched.
2. **Earth candidate data** identifies locations that can plausibly serve as terrestrial analogs.
3. Both sides enter the **same feature pipeline**, making their derived characteristics directly comparable.
4. Individual factors receive similarity scores from **0 to 1**.
5. The engineering purpose determines the **weights** applied to those factors.
6. Candidate windows receive a weighted score and are **ranked**.
7. The resulting locations are compared with known analog sites and explicit limitations are preserved.

### Primary pipeline

```text
Moon reference ──┐
                 ├══> Shared Feature Pipeline
Earth candidates ┘              ║
                                ▼
                       Factor Similarity
                                ║
                                ▼
Engineering Purpose ──> Weights ══> Weighted Score
                                      ║
                                      ▼
                                    Rank
                                      ║
                                      ▼
                                  Earth Sites
                                      │
                           ┌──────────┴──────────┐
                           ▼                     ▼
                     Validation             Limitations
```