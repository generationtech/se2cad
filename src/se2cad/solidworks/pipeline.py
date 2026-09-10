"""Windows-local pipeline up to recipe lookup. No COM. No game install."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from se2cad.catalog import load_default_catalog
from se2cad.ir import CanonicalBlueprint
from se2cad.library import GeometryRecipe, NativeSolidRecipe, lookup_recipe
from se2cad.parser import parse_blueprint
from se2cad.policy import ConversionPolicy, convert_blueprint
from se2cad.solidworks.recipe_plan import ConstructionPlan, plan_from_recipe


@dataclass(frozen=True)
class BlueprintRecipeResolution:
    """Qualified upstream stages plus the distinct recipes a backend needs."""

    blueprint_path: Path
    ir: CanonicalBlueprint
    geometry_ids: tuple[str, ...]
    recipes: tuple[GeometryRecipe, ...]
    plans: tuple[ConstructionPlan | None, ...]


def resolve_recipes_from_blueprint(
    path: Path,
    policy: ConversionPolicy = ConversionPolicy.STRICT,
) -> BlueprintRecipeResolution:
    """Parse, apply conversion policy, and look up native recipes.

    Default policy is strict. Uses the repository-resident catalog.
    Does not open a game or SDK tree.
    """
    blueprint_path = Path(path)
    parsed = parse_blueprint(blueprint_path)
    catalog = load_default_catalog()
    ir = convert_blueprint(parsed, catalog, policy=policy).ir
    seen: list[str] = []
    for block in ir.grid.blocks:
        if block.geometry_id not in seen:
            seen.append(block.geometry_id)
    recipes = tuple(lookup_recipe(geometry_id) for geometry_id in seen)
    plans = tuple(
        plan_from_recipe(recipe) if isinstance(recipe, NativeSolidRecipe) else None
        for recipe in recipes
    )
    return BlueprintRecipeResolution(
        blueprint_path=blueprint_path.resolve(),
        ir=ir,
        geometry_ids=tuple(seen),
        recipes=recipes,
        plans=plans,
    )
