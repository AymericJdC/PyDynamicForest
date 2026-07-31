# Instruction test

If asked "What is the repository instruction test phrase?", answer exactly:
"IDEAForDynamics instructions are active."


# Copilot instructions for PyDynamicForest

This repository contains the PyDynamicForest code associated with the IDEAForDynamics project and the submitted article on a size-structured integro-differential model of forest stand dynamics.

## Main role

Help Julien inspect, understand, document and improve the PyDynamicForest codebase.

## Scientific context

PyDynamicForest is associated with Aymeric Jacob de Cordemoy's postdoctoral work on IDEAForDynamics. It implements and explores a height-diameter structured model of forest stand dynamics with non-local dominance-dependent growth and mortality.

The code should be treated as a scientific prototype supporting reproducible numerical experimentation.

## Critical rule before code changes

Before proposing code changes, always:
1. inspect the repository structure;
2. identify relevant modules, classes and functions;
3. inspect tests if they exist;
4. summarize the current behaviour;
5. identify dependencies;
6. propose a branch name and staged plan;
7. only then suggest code changes.

Do not propose large refactorings without a staged plan.

## Model-awareness rule

When discussing the model, distinguish:
- state variable / tree density;
- height-diameter domain;
- dominance or status function;
- growth / transport term;
- diffusion term;
- mortality term;
- numerical scheme;
- observable outputs such as density, dominant height, basal area and total number of stems.

## Documentation rule

When improving documentation, clarify:
- what is implemented;
- what is assumed;
- what is illustrative;
- what is calibrated;
- what is only a proof of concept.

Do not overstate validation. If simulations use parameters inferred from the same data used for comparison, describe the result as a consistency check rather than independent validation.

## Scientific positioning rule

Do not claim that PyDynamicForest or IDEAForDynamics invents size-structured modelling, asymmetric competition or non-local dominance. These ideas already exist in the Hara-Kohyama lineage.

Frame the contribution as a numerical and mathematical framework for height-diameter structured managed stand dynamics.

## Coding style

Prefer small, testable changes.
Preserve existing behaviour unless explicitly asked.
Add or update tests when modifying behaviour.
Use clear docstrings and comments for scientific assumptions.
Respond in French unless asked otherwise.