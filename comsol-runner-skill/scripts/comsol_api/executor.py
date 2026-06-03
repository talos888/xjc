from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import (
    GEOMETRY_FEATURES,
    PHYSICS_FEATURES,
    PHYSICS_INTERFACES,
    STUDY_TYPES,
    api_type_for,
)


def set_properties(feature, properties: dict[str, Any] | None) -> None:
    for key, value in (properties or {}).items():
        if isinstance(value, list):
            feature.set(str(key), [str(item) for item in value])
        else:
            feature.set(str(key), str(value))


def apply_selection(feature, selection: Any) -> None:
    if selection is None:
        return
    selector = feature.selection()
    if selection == "all":
        selector.all()
        return
    if isinstance(selection, dict):
        if selection.get("all"):
            selector.all()
            return
        if "named" in selection:
            selector.named(str(selection["named"]))
            return
        if "entities" in selection:
            selector.set(selection["entities"])
            return
    selector.set(selection)


class OfficialPlanExecutor:
    """Execute a literature/planner-derived plan through COMSOL Java API calls."""

    def __init__(self, model, plan: dict[str, Any]):
        self.model = model
        self.java = model.java
        self.plan = plan

    def apply_parameters(self) -> None:
        for key, value in self.plan.get("parameters", {}).items():
            self.model.parameter(str(key), str(value))

    def build_components(self) -> None:
        components = self.plan.get("components", [])
        if not components:
            raise ValueError("Plan must contain at least one component.")
        for component in components:
            self._build_component(component)

    def _build_component(self, component: dict[str, Any]) -> None:
        tag = str(component.get("tag", "comp1"))
        dimension = int(component.get("dimension", 2))
        geom_tag = str(component.get("geometry", {}).get("tag", "geom1"))
        mesh_tag = str(component.get("mesh", {}).get("tag", "mesh1"))

        self.java.component().create(tag, True)
        self.java.component(tag).geom().create(geom_tag, dimension)
        self.java.component(tag).mesh().create(mesh_tag)

        self._build_geometry(tag, geom_tag, component.get("geometry", {}))
        self._build_selections(tag, geom_tag, component.get("selections", []))
        self._build_materials(tag, component.get("materials", []))
        self._build_physics(tag, geom_tag, component.get("physics", []))
        self._build_mesh(tag, mesh_tag, component.get("mesh", {}))

    def _build_geometry(self, component_tag: str, geom_tag: str, geometry: dict[str, Any]) -> None:
        geom = self.java.component(component_tag).geom(geom_tag)
        for item in geometry.get("features", []):
            api_type = api_type_for(GEOMETRY_FEATURES, item, "Geometry feature")
            tag = str(item["tag"])
            geom.create(tag, api_type)
            set_properties(geom.feature(tag), item.get("properties"))
        geom.run()

    def _build_selections(
        self, component_tag: str, geom_tag: str, selections: list[dict[str, Any]]
    ) -> None:
        component = self.java.component(component_tag)
        for selection in selections:
            tag = str(selection["tag"])
            api_type = str(selection["api_type"])
            component.selection().create(tag, api_type)
            selection_obj = component.selection(tag)
            if "label" in selection:
                selection_obj.label(str(selection["label"]))
            if "dimension" in selection:
                selection_obj.geom(geom_tag, int(selection["dimension"]))
            if selection.get("all"):
                selection_obj.all()
            elif "entities" in selection:
                selection_obj.set(selection["entities"])
            set_properties(selection_obj, selection.get("properties"))

    def _build_materials(self, component_tag: str, materials: list[dict[str, Any]]) -> None:
        component = self.java.component(component_tag)
        for material in materials:
            tag = str(material["tag"])
            component.material().create(tag, str(material.get("type", "Common")))
            feature = component.material(tag)
            if "label" in material:
                feature.label(str(material["label"]))
            apply_selection(feature, material.get("selection"))
            for group in material.get("property_groups", []):
                group_tag = str(group.get("tag", "def"))
                props = feature.propertyGroup(group_tag)
                for key, value in group.get("properties", {}).items():
                    if isinstance(value, list):
                        props.set(str(key), [str(item) for item in value])
                    else:
                        props.set(str(key), str(value))

    def _build_physics(
        self, component_tag: str, geom_tag: str, physics_entries: list[dict[str, Any]]
    ) -> None:
        component = self.java.component(component_tag)
        for physics in physics_entries:
            api_type = api_type_for(PHYSICS_INTERFACES, physics, "Physics interface")
            tag = str(physics["tag"])
            component.physics().create(tag, api_type, geom_tag)
            interface = component.physics(tag)
            if "label" in physics:
                interface.label(str(physics["label"]))
            if "field" in physics:
                field = physics["field"]
                interface.field(str(field.get("tag", "field"))).field(str(field["name"]))
                if "components" in field:
                    interface.field(str(field.get("tag", "field"))).component(
                        [str(item) for item in field["components"]]
                    )
            for feature in physics.get("features", []):
                self._create_physics_feature(interface, feature)

    def _create_physics_feature(self, interface, feature_spec: dict[str, Any]) -> None:
        tag = str(feature_spec["tag"])
        if not feature_spec.get("existing", False):
            api_type = api_type_for(PHYSICS_FEATURES, feature_spec, "Physics feature")
            dimension = int(feature_spec.get("dimension", 1))
            interface.create(tag, api_type, dimension)
        feature = interface.feature(tag)
        apply_selection(feature, feature_spec.get("selection"))
        set_properties(feature, feature_spec.get("properties"))

    def _build_mesh(self, component_tag: str, mesh_tag: str, mesh: dict[str, Any]) -> None:
        mesh_obj = self.java.component(component_tag).mesh(mesh_tag)
        if "auto_size" in mesh:
            mesh_obj.autoMeshSize(int(mesh["auto_size"]))
        if mesh.get("run", True):
            mesh_obj.run()

    def build_studies(self) -> None:
        for study in self.plan.get("studies", []):
            tag = str(study.get("tag", "std1"))
            self.java.study().create(tag)
            for feature in study.get("features", []):
                api_type = api_type_for(STUDY_TYPES, feature, "Study feature")
                feature_tag = str(feature["tag"])
                self.java.study(tag).create(feature_tag, api_type)
                set_properties(self.java.study(tag).feature(feature_tag), feature.get("properties"))

    def run_studies(self) -> None:
        for study in self.plan.get("studies", []):
            if study.get("run", True):
                self.java.study(str(study.get("tag", "std1"))).run()

    def build_results(self) -> None:
        for result in self.plan.get("results", []):
            tag = str(result["tag"])
            self.java.result().create(tag, str(result["api_type"]))
            plot_group = self.java.result(tag)
            if "label" in result:
                plot_group.label(str(result["label"]))
            set_properties(plot_group, result.get("properties"))
            for feature in result.get("features", []):
                ftag = str(feature["tag"])
                plot_group.feature().create(ftag, str(feature["api_type"]))
                if "label" in feature:
                    plot_group.feature(ftag).label(str(feature["label"]))
                set_properties(plot_group.feature(ftag), feature.get("properties"))
            if result.get("run", True):
                plot_group.run()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
