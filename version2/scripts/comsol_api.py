from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any


def java_int_array(values: Iterable[int]) -> Any:
    import jpype

    return jpype.JArray(jpype.JInt)([int(value) for value in values])


def validate_tensor3(values: Sequence[Any], label: str = "tensor") -> list[str]:
    flat = [str(value) for value in values]
    if len(flat) != 9:
        raise ValueError(f"{label}_must_have_9_entries: got {len(flat)}")
    return flat


def assert_count(actual: int, expected: int, label: str) -> None:
    if int(actual) != int(expected):
        raise ValueError(f"{label}_count_mismatch: expected {expected}, got {actual}")


def configure_floquet_periodic(
    feature: Any,
    pair_selection: str,
    destination_selection: str,
    k_vector: Sequence[str] = ("0", "0", "0"),
) -> None:
    feature.selection().named(pair_selection)
    feature.set("manualDestinationSelection", True)
    feature.selection("destinationDomains").named(destination_selection)
    feature.set("PeriodicType", "Floquet")
    feature.set("Floquet_source", "UserDefined")
    feature.set("kFloquet", list(k_vector))


def configure_relative_permittivity(feature: Any, tensor: Sequence[Any]) -> None:
    feature.set("epsilonr_mat", "userdef")
    feature.set("epsilonr", validate_tensor3(tensor, "relative_permittivity"))


def direct_frequency_expression(wavelength_expression: str) -> str:
    return f"c_const/({wavelength_expression})"


def add_native_results(
    model_java: Any,
    dataset: str,
    spectrum_expressions: Sequence[str],
    spectrum_labels: Sequence[str],
    field_expression: str,
) -> dict[str, str]:
    result = model_java.result()
    result.create("pg_spectra", "PlotGroup1D")
    model_java.result("pg_spectra").label("Reflection and transmission spectra")
    model_java.result("pg_spectra").set("data", dataset)
    model_java.result("pg_spectra").create("glob_spectra", "Global")
    model_java.result("pg_spectra").feature("glob_spectra").set("expr", list(spectrum_expressions))
    model_java.result("pg_spectra").feature("glob_spectra").set("descr", list(spectrum_labels))

    result.create("pg_field", "PlotGroup2D")
    model_java.result("pg_field").label(f"Field map: {field_expression}")
    model_java.result("pg_field").set("data", dataset)
    model_java.result("pg_field").create("surf_field", "Surface")
    model_java.result("pg_field").feature("surf_field").set("expr", field_expression)

    result.table().create("tbl_spectra", "Table")
    result.table("tbl_spectra").label("Spectral data")
    result.numerical().create("gev_spectra", "EvalGlobal")
    result.numerical("gev_spectra").label("Reflection and transmission")
    result.numerical("gev_spectra").set("data", dataset)
    result.numerical("gev_spectra").set("expr", list(spectrum_expressions))
    result.numerical("gev_spectra").set("descr", list(spectrum_labels))
    result.numerical("gev_spectra").set("table", "tbl_spectra")
    return {
        "spectrum_plot": "pg_spectra",
        "field_plot": "pg_field",
        "spectrum_table": "tbl_spectra",
        "spectrum_evaluation": "gev_spectra",
    }
