# Future Direction — ML / Predictive Layer

## Idea

Once the core map application is stable, a natural next step is adding a **predictive risk scoring model** — moving from "where did fatalities happen" to "where are fatalities likely to happen."

## What this could look like

Given the FARS dataset (1975–2022) contains rich feature data (time of day, road type, lighting, speed limit, weather, etc.), a model could be trained to:

- Score any road segment or intersection for pedestrian fatality risk
- Predict high-risk zones based on environmental/infrastructure features
- Highlight under-reported areas that share characteristics with known danger spots

This transforms the tool from a historical map into a genuine planning tool.

## Tooling to watch — autoresearch

Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) project demonstrates AI agents autonomously running ML experiments overnight — iterating on model architecture, hyperparameters, and training scripts via a git loop on a single GPU.

The concept is relevant here: once a baseline model exists (e.g. scikit-learn risk scorer, small PyTorch classifier), autoresearch-style tooling could automate:
- Experimenting with different feature sets (what inputs matter most?)
- Hyperparameter search
- Comparing clustering algorithms for spatial risk zones

## Practical starting point

Before autoresearch-level tooling is relevant, the simpler path is:
1. Get the core map app running (current priority)
2. Add a basic scikit-learn logistic regression or random forest risk scorer trained on FARS features
3. Visualize risk scores as a heatmap layer alongside raw fatality data
4. Then explore automated experimentation if the model warrants it

## References

- [autoresearch GitHub](https://github.com/karpathy/autoresearch)
- [VentureBeat overview](https://venturebeat.com/technology/andrej-karpathys-new-open-source-autoresearch-lets-you-run-hundreds-of-ai)
