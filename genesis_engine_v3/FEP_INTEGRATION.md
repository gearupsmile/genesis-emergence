# FEP Integration: Genesis V3 through the Lens of Active Inference

This document maps the mechanical features of Genesis v3 to the theoretical framework of the **Free Energy Principle (FEP)** and **Active Inference**.

## 1. Niche Construction as Active Inference

**Genesis Feature:** Secretion Physics (`Substrate.S`, `Agent.secrete()`)

**FEP Concept:** **Active Inference** (changing the world to fit expectations)

In FEP, biological systems minimize "surprise" (free energy) in two ways:
1.  **Perception**: Updating internal models to match sensory data.
2.  **Action**: Changing the world (sensory data) to match internal models.

In Genesis v3, **Secretion** represents the second path. By modifying the external environment (depositing `S`), agents perform **Niche Construction**. They create a formatted local environment that may be more predictable or favorable for their offspring (e.g., if `S` signals safety or resource availability).

*   *Real Mode* allows Active Inference via niche construction.
*   *Sham Mode* blocks the causal link between Action and Environmental Change, forcing agents to rely solely on internal adaptation (Perception/Evolution).

## 2. The Markov Blanket & Environmental Snapshots

**Genesis Feature:** AIS Archive (`Genome` + `Environment Snapshot`)

**FEP Concept:** **The Markov Blanket** and **Generative Models**

The **Markov Blanket** defines the boundary between the Agent (internal states) and the World (external states).
-   **Genome**: Represents the agent's **Generative Model** (its blueprint for predicting/surviving the world).
-   **Environment Snapshot**: Represents the **Sensory States** at the boundary of the blanket.

By archiving the *pair* `(Genome, Snapshot)`, we capture the **Agent-Environment System** state. This allows us to analyze how Generative Models (Genomes) co-evolve with the External States they are trying to predict/control.

## 3. Complexity & The Edge of Chaos

**Genesis Feature:** LZ Complexity on Action Traces

**FEP Concept:** **Complexity Minimization** / **Self-Organization**

FEP suggests living systems engage in "self-evidencing" behavior that balances:
-   **Accuracy**: Minimizing prediction error (surviving).
-   **Complexity**: Minimizing model complexity (efficiency).

However, in a dynamic world, the *optimal* behavior is rarely static (LZ ~ 0) or random (LZ ~ Max). It is structured.
-   **Low LZ**: maladaptive stasis (looping).
-   **High LZ (Random)**: maladaptive noise (failure to predict).
-   **Intermediate/Structured LZ**: Evidence of complex adaptive behavior, potentially correlating with "Criticality" or the "Edge of Chaos".

## 4. Metabolic Cost as Variational Free Energy

**Genesis Feature:** Metabolic Cost of Secretion (paid in both Real and Sham)

**FEP Concept:** **Thermodynamic Constraints**

Minimizing Variational Free Energy is analogous to minimizing metabolic potential to maintain homeostasis. Action is expensive.
-   The **Sham Control** proves that the *informational/physical gain* of modifying the environment (Real Mode) must outweigh this metabolic cost for the behavior to be selected.
-   If `Secretion` persists in Real Mode but vanishes in Sham Mode (evolutionarily), it proves that the **Action-Perception Loop** (environmental feedback) provides a fitness advantage (reduction in surprise) greater than the energy cost.

---

## Summary Mapping

| Genesis v3 Component | FEP / Active Inference Term |
|----------------------|-----------------------------|
| **Agent** | **Generative Model / Phenotype** |
| **Genome** | **Prior Beliefs / Model Parameters** |
| **Environment (`S` Field)** | **Generative Process / External States** |
| **Sensing/Inputs** | **Sensory States** |
| **Actions ('M', 'S')** | **Active States** |
| **Secretion (`S`)** | **Niche Construction / Active Inference** |
| **Metabolic Cost** | **Free Energy / Thermodynamic Cost** |
| **AIS Purging** | **Model Selection / Surprise Minimization (Death)** |

This framing moves Genesis from a simple "survival of the fittest" simulation to a testbed for **Extended Evolutionary Synthesis** and **Active Inference**.
