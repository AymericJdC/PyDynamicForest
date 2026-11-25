"""Q-9E.4 orchestration from assigned heights to conservative grid states."""
from __future__ import annotations
from dataclasses import dataclass
from .grid_projection import *

@dataclass(frozen=True)
class AnnualGridReconstruction:
    year:int; state:ProjectedState; diagnostics:ProjectionDiagnostics

def reconstruct_grid_state(trees,assignment,height_nodes_m,diameter_nodes_cm,boundary_policy=BoundaryPolicy.STRICT):
    grid=ProjectionGrid(height_nodes_m,diameter_nodes_cm)
    state=project_trees_to_grid(trees,assignment,grid,boundary_policy)
    diagnostics=projection_diagnostics(trees,assignment,state)
    return AnnualGridReconstruction(assignment.context.year,state,diagnostics)
