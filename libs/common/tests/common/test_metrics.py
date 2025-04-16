import pytest
from aioprometheus import Registry, Gauge, Histogram

from common.metrics import get_or_create_metric


def test_get_or_create_metric():
    registry = Registry()

    with pytest.raises(KeyError):
        registry.get("not_found")

    gauge = get_or_create_metric(registry, "not_found", Gauge, "doc")

    assert gauge is not None
    assert gauge == registry.get("not_found")
    assert gauge == get_or_create_metric(registry, "not_found", Gauge, "doc")

    assert gauge.name == "not_found"
    assert gauge.doc == "doc"

    with pytest.raises(KeyError):
        registry.get("not_found_histogram")


def test_get_or_create_metric_with_extra_args():
    registry = Registry()
    histogram = get_or_create_metric(
        registry,
        "not_found_histogram",
        Histogram,
        doc="doc_histogram",
        const_labels={"app": "test"},
        buckets=[0.1, 0.2, 0.5],
    )

    assert histogram is not None
    assert histogram == registry.get("not_found_histogram")

    assert histogram.name == "not_found_histogram"
    assert histogram.doc == "doc_histogram"
    assert histogram.const_labels == {"app": "test"}
    assert histogram.upper_bounds == [0.1, 0.2, 0.5]


def test_get_or_create_metric_redefine():
    registry = Registry()
    get_or_create_metric(
        registry,
        "not_found_histogram",
        Histogram,
        doc="doc_histogram",
        const_labels={"app": "test"},
        buckets=[0.1, 0.2, 0.5],
    )

    with pytest.raises(ValueError) as execinfo:
        get_or_create_metric(registry, "not_found_histogram", Gauge, doc="redefining")
    assert (
        str(execinfo.value)
        == "Metric not_found_histogram was requested with a different type that it was originally built. Histogram is not Gauge"
    )


def test_get_or_create_metric_different_registries():
    registry = Registry()
    registry2 = Registry()
    histogram = get_or_create_metric(
        registry,
        "not_found_histogram",
        Histogram,
        doc="doc_histogram",
        const_labels={"app": "test"},
        buckets=[0.1, 0.2, 0.5],
    )
    gauge = get_or_create_metric(
        registry2, "not_found_histogram", Gauge, doc="redefining in other registry"
    )

    assert histogram is not gauge
