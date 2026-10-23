"""Non-mutating validation of height assignments."""
from __future__ import annotations
from dataclasses import dataclass
from .height_types import *
import math

@dataclass(frozen=True)
class ValidationIssue:
    severity:str; code:str; tree_id:str|int|None; year:int|None; message:str
@dataclass(frozen=True)
class HeightValidationResult:
    is_valid:bool; status:str; n_total:int; n_valid:int; n_missing:int; n_invalid:int; issues:tuple[ValidationIssue,...]
@dataclass(frozen=True)
class HeightValidationPolicy:
    minimum_height_m:float=0.0; maximum_height_m:float|None=None; allow_missing:bool=True; require_uncertainty:bool=False
    def validate(self,trees,assignment):
        issues=[]; keys=[(t.tree_id,t.year) for t in trees]; hs=[(h.tree_id,h.year) for h in assignment.heights]
        for key in set(keys):
            if keys.count(key)>1: issues.append(ValidationIssue("error","duplicate_tree_key",key[0],key[1],"duplicate input tree key"))
        for key in set(hs):
            if hs.count(key)>1: issues.append(ValidationIssue("error","duplicate_assignment",key[0],key[1],"duplicate assigned height"))
        for key in set(keys)-set(hs): issues.append(ValidationIssue("error","missing_assignment",key[0],key[1],"no assignment returned"))
        for key in set(hs)-set(keys): issues.append(ValidationIssue("error","unexpected_assignment",key[0],key[1],"assignment has no input tree"))
        nvalid=nmissing=ninvalid=0
        for h in assignment.heights:
            if h.is_missing:
                nmissing+=1
                if not self.allow_missing: issues.append(ValidationIssue("error","missing_not_allowed",h.tree_id,h.year,h.missing_reason or "missing"))
                continue
            bad=(h.height_m is None or not math.isfinite(h.height_m) or h.height_m<self.minimum_height_m or (self.maximum_height_m is not None and h.height_m>self.maximum_height_m))
            if bad:
                ninvalid+=1; issues.append(ValidationIssue("error","height_out_of_bounds",h.tree_id,h.year,"height is outside the validation policy"))
            else: nvalid+=1
            if self.require_uncertainty and h.uncertainty.kind in {UncertaintyKind.UNKNOWN,UncertaintyKind.NOT_APPLICABLE}:
                issues.append(ValidationIssue("warning","uncertainty_not_quantified",h.tree_id,h.year,"uncertainty is not quantified"))
        errors=sum(i.severity=="error" for i in issues); warnings=sum(i.severity=="warning" for i in issues)
        status="invalid" if errors else ("valid_with_warning" if warnings else "valid")
        return HeightValidationResult(not errors,status,len(trees),nvalid,nmissing,ninvalid,tuple(issues))
