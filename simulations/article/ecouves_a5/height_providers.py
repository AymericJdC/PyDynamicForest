"""Generic, allometry-independent height providers."""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any
from .height_types import *

class HeightProvider(ABC):
    def __init__(self, metadata: HeightProviderMetadata): self.metadata=metadata
    @abstractmethod
    def assign_heights(self, trees: Sequence[TreeRecord], context: StandContext) -> HeightAssignment: ...
    def _finish(self, trees, context, heights, warnings=()):
        hs=tuple(heights); expected=[(t.tree_id,t.year) for t in trees]; actual=[(h.tree_id,h.year) for h in hs]
        if len(actual)!=len(expected) or set(actual)!=set(expected): raise ValueError("provider must return exactly one height per input tree")
        return HeightAssignment(context,self.metadata,hs,tuple(warnings))

def _missing(tree, meta, reason):
    return AssignedHeight(tree.tree_id,tree.year,None,True,reason,meta.provider_id,meta.category,meta.source,HeightUncertainty(UncertaintyKind.UNKNOWN))
def _assigned(tree,meta,height,uncertainty=None,metadata=None):
    return AssignedHeight(tree.tree_id,tree.year,float(height),False,None,meta.provider_id,meta.category,meta.source,uncertainty or HeightUncertainty(UncertaintyKind.UNKNOWN),metadata or {})

class ObservedHeightProvider(HeightProvider):
    def __init__(self, observations: Mapping[tuple[Any,int],float] | Iterable[tuple[Any,int,float]], provider_id="observed", source=None):
        items=list(observations.items()) if isinstance(observations,Mapping) else [((a,b),c) for a,b,c in observations]
        data={}
        for key,value in items:
            if key in data: raise ValueError(f"duplicate observed height for {key}")
            data[key]=float(value)
        self.observations=data
        super().__init__(HeightProviderMetadata(provider_id,"Observed heights","1",ProviderCategory.OBSERVED,True,source=source))
    def assign_heights(self,trees,context):
        return self._finish(trees,context,[_assigned(t,self.metadata,self.observations[(t.tree_id,t.year)],HeightUncertainty(UncertaintyKind.NOT_APPLICABLE)) if (t.tree_id,t.year) in self.observations else _missing(t,self.metadata,"observation_not_available") for t in trees])

class FixedHeightProvider(HeightProvider):
    def __init__(self,height_m:float,uncertainty:HeightUncertainty|None=None):
        self.height_m=float(height_m); self.uncertainty=uncertainty
        super().__init__(HeightProviderMetadata("fixed-test","Fixed test height","1",ProviderCategory.FIXED_TEST,True,"Testing only"))
    def assign_heights(self,trees,context): return self._finish(trees,context,[_assigned(t,self.metadata,self.height_m,self.uncertainty) for t in trees])

class CallableHeightProvider(HeightProvider):
    def __init__(self,func:Callable[[TreeRecord,StandContext],Any],provider_id="callable",name="Callable height provider",version="1",source=None):
        self.func=func; super().__init__(HeightProviderMetadata(provider_id,name,version,ProviderCategory.CALLABLE,True,source=source))
    def assign_heights(self,trees,context):
        out=[]
        for t in trees:
            value=self.func(t,context)
            if isinstance(value,AssignedHeight):
                if (value.tree_id,value.year)!=(t.tree_id,t.year): raise ValueError("callable returned a mismatched tree key")
                out.append(value)
            elif value is None: out.append(_missing(t,self.metadata,"callable_returned_missing"))
            elif isinstance(value,tuple): out.append(_assigned(t,self.metadata,value[0],value[1] if len(value)>1 else None))
            else: out.append(_assigned(t,self.metadata,value))
        return self._finish(trees,context,out)

class MissingHeightProvider(HeightProvider):
    def __init__(self,reason="height_source_not_available"):
        self.reason=reason; super().__init__(HeightProviderMetadata("missing","Missing height provider","1",ProviderCategory.MISSING,True))
    def assign_heights(self,trees,context): return self._finish(trees,context,[_missing(t,self.metadata,self.reason) for t in trees])

class CompositeHeightProvider(HeightProvider):
    def __init__(self,providers:Sequence[HeightProvider],provider_id="composite"):
        if not providers: raise ValueError("at least one provider is required")
        self.providers=tuple(providers); super().__init__(HeightProviderMetadata(provider_id,"Composite height provider","1",ProviderCategory.COMPOSITE,all(p.metadata.deterministic for p in providers)))
    def assign_heights(self,trees,context):
        unresolved=list(trees); resolved={}; warnings=[]
        for provider in self.providers:
            if not unresolved: break
            batch=provider.assign_heights(tuple(unresolved),context)
            bykey={(h.tree_id,h.year):h for h in batch.heights}
            next_unresolved=[]
            for t in unresolved:
                h=bykey[(t.tree_id,t.year)]
                if h.is_missing: next_unresolved.append(t)
                else: resolved[(t.tree_id,t.year)]=h
            unresolved=next_unresolved; warnings.extend(batch.warnings)
        for t in unresolved:
            resolved[(t.tree_id,t.year)]=_missing(t,self.metadata,"all_composite_providers_missing")
        ordered=[resolved[(t.tree_id,t.year)] for t in trees]
        return self._finish(trees,context,ordered,warnings)
