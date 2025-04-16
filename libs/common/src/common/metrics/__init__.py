from typing import Optional, TypeVar

from aioprometheus import Registry
from aioprometheus.collectors import Collector, LabelsType

T = TypeVar("T", bound=Collector)


def get_or_create_metric(
    registry: Registry,
    name: str,
    collector: type[T],
    doc: str,
    const_labels: Optional[LabelsType] = None,
    **kwargs,
) -> T:
    if name in registry.collectors:
        metric = registry.get(name)
        if type(metric) is not collector:
            raise ValueError(
                f"Metric {name} was requested with a different type that it was originally built. {type(metric).__name__} is not {collector.__name__}"
            )
        return metric
    return collector(
        name=name, doc=doc, const_labels=const_labels, registry=registry, **kwargs
    )
