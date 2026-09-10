"""Single human-authorized SDK-mesh catalog bind (S2C-11.7.1).

This is not general TriangleMesh support. Other identities stay leftover
or unknown. Selection and leftover honesty import these tokens only.
"""

from __future__ import annotations

from se2cad.catalog.model import CatalogEntry, RecipeKind, SupportStatus

AUTHORIZED_SDK_MESH_SUBTYPE_ID = "LargeBlockSmallHydrogenThrust"
AUTHORIZED_SDK_MESH_GEOMETRY_ID = "large_block_small_hydrogen_thrust"
AUTHORIZED_SDK_MESH_RECIPE_KIND = RecipeKind.SDK_MESH_DIRECT


def is_authorized_sdk_mesh_entry(entry: CatalogEntry) -> bool:
    """True only for the explicit S2C-11.7.1 catalog bind."""
    return (
        entry.subtype_id == AUTHORIZED_SDK_MESH_SUBTYPE_ID
        and entry.geometry_id == AUTHORIZED_SDK_MESH_GEOMETRY_ID
        and entry.recipe_kind is AUTHORIZED_SDK_MESH_RECIPE_KIND
        and entry.support_status is SupportStatus.SUPPORTED
    )
