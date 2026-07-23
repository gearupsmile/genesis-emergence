# Genesis Presentation Diagrams

This directory contains six high-resolution, publication-ready block diagrams (300 DPI, white background) representing the core systems and algorithms of the **Genesis** artificial life engine.

## Diagram Index

### 1. `genesis_diag1.png` – High-Level Conceptual Loop
* **Title**: *Genesis Core Loop (No Fitness)*
* **Content**: Displays the objective-free evolutionary cycle:
  $$\text{Agents} \leftrightarrow \text{Environment} \leftrightarrow \text{Selection} \leftrightarrow \text{Reproduction} \leftrightarrow \text{Mutation}$$
* **Purpose**: Illustrates that selection is purely constraint-driven, showing that agents must survive inside a viability corridor without climbing a pre-programmed fitness slope.

### 2. `genesis_diag2.png` – Agent Representation & Genetics
* **Title**: *Agent Representation & Genetics*
* **Content**: Details agent internals:
  * **Sensory Inputs** (coordinates, energy, chemical gradients) mapped via a **CPPN Controller** to the **Action Space** (move, secrete, idle).
  * **NEAT Speciation Callout**: Shows the compatibility distance formula ($\delta$) used to protect topological structural mutations from early culling.
  * **Metabolic Cost Callout**: Formulates the superlinear complexity penalty ($\text{Cost} = 0.02 \cdot G^{1.8}$) which blocks reproduction if energy is insufficient.

### 3. `genesis_diag3.png` – Environment Physics
* **Title**: *Environment Physics*
* **Content**: Visualizes substrate feedback loops:
  * **Gray-Scott Substrate**: Equations regulating chemical energy ($U$) and activator ($V$) fields.
  * **Secretion Substrate**: Equations for chemical trail ($S$) diffusion ($D_s=0.1$) and decay ($\gamma_s=0.01$) deposited by agents in a $3\times3$ neighborhood.
  * **CPPN Parameter Maps**: Illustrates how heterogeneous feed ($F$) and kill ($k$) rates are generated dynamically.

### 4. `genesis_diag4.png` – Selection & Regulation
* **Title**: *Selection & Regulation – Constraint-Driven*
* **Content**: Flowchart mapping viability checks:
  1. **Physics Gatekeeper**: Binary life/death check ($Cost \le 0.5$).
  2. **Pareto Dominance**: Multi-objective selection across three efficiency axes.
  3. **AIS**: Stateless relevance decay and purging rules.
  4. **CARP Autoregulation**: Closed-loop proportional controller adjusting viability margins.

### 5. `genesis_diag5.png` – Co-evolutionary Orchestrator (POET-style)
* **Title**: *Co-evolutionary Orchestrator (V5)*
* **Content**: Swimlane layout tracing co-evolutionary steps:
  * Environmental mutation $\rightarrow$ **Goldilocks Filter** check (survival variance) $\rightarrow$ **PATA-EC Novelty Filter** ranking correlation check ($\rho \le 0.9$) $\rightarrow$ Niche pool goal-switching transfers $\rightarrow$ **ANNEX** unique fingerprint archiving.

### 6. `genesis_diag6.png` – Full System Integration
* **Title**: *Genesis Full Stack*
* **Content**: Layered diagram showing the hierarchical boundaries:
  1. **Co-evolutionary Curriculum Layer** (Top)
  2. **Core Simulation Layer** (Middle)
  3. **Selection & Regulation Layer** (Bottom)
* **Legend**: Distinguishes solid lines (physical interactions/selection) from dashed lines (information/curriculum flow).

---

## Technical Specifications
* **Resolution**: 300 DPI (approx. $3600 \times 2700$ pixels)
* **Background**: Solid white (`#FFFFFF`) for slide visibility
* **Typography**: Arial / Helvetica (10-12pt for details, 14-16pt for headers)
* **Style**: Minimalist, high-contrast, publication-grade layout
