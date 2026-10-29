---
name: image-to-3d
description: "Convert a user-supplied image into one textured 3D asset using Blender MCP: validate the reference, generate a single model, normalize scale/origin/grounding, inspect mesh/materials, and export GLB plus preview. Use for image-to-3D, picture-to-model, generated game props, or Blender asset production. Requires an image path or URL and a running Blender addon for actual generation."
version: "1.0.0"
metadata:
  related_skills: [jebat-creative, image, gits-dual-plane-isometric-assets]
---

# Image to 3D

Produce one reviewed, textured 3D asset from one user-supplied image. Do not substitute text generation when the user requested image-based conversion.

## Required input

- Absolute local image path or `http(s)` image URL.
- Intended real-world dimensions or an explicit normalization target.
- Destination/use: Blender scene, GLB, game engine, or preview.

If no image was supplied, request one. Do not silently use a text prompt instead. Do not guess which installed object or image the user means.

## Reference requirements

- One coherent object, fully visible, centered, with clear silhouette.
- Plain/uncluttered background, even lighting, no text, watermark, hands, or scene clutter.
- Front three-quarter view preferred; hidden surfaces are inferred and must be treated as uncertain.
- User owns the image or has permission to transform it.

## Workflow

1. **Check Blender.** Call `get_addon_status` once and `get_scene_info` to understand the destination scene. If Blender is unreachable, stop before generation and report that prerequisite.
2. **Validate source.** Confirm the image exists/readable or URL returns an image. Record source path/URL; do not send it to another service outside the chosen generator workflow.
3. **Generate one asset.** Call `generate_3d(image=..., name=..., user_prompt=<verbatim request>)`. No scene, ground, or separate assembly parts. Generation can cost a credit; do not retry a completed request or generate variants without approval.
4. **Resume, not duplicate.** If a job handle is returned, call `generate_3d(job=..., name=...)` to continue waiting.
5. **Inspect import.** Read reported world bounding box and object identity. Generated assets arrive at arbitrary scale/facing.
6. **Normalize.** Set origin at bottom-center, uniform scale to requested dimensions, rotate upright, place lowest bound on ground. Never alter unrelated scene objects.
7. **Review.** Use `get_scene_info` and `look`. Inspect silhouette, topology, normals, textures/materials, floating/intersecting geometry, and orientation. Hidden-side artifacts remain a limitation.
8. **Export.** Export the selected asset only as GLB with textures, plus a preview PNG. Preserve source image and record generator/provider, source, dimensions, and validation status.
9. **Deliver.** Report file paths, actual checks, and remaining geometry/material limitations. Generation success alone is not asset approval.

## Blender execution rules

- Look up shader nodes by `type`, never localized names.
- Read enum values instead of hardcoding identifiers.
- Material colors belong on shader inputs, not just `diffuse_color`.
- Work in small reversible steps. Do not delete or replace existing scene content.
- Duplicate an accepted model for repeats; do not pay to regenerate identical props.

## Acceptance gates

- Correct source object and coherent silhouette.
- One imported asset; no unwanted scene/ground objects.
- Requested scale, upright orientation, bottom-center origin, ground contact.
- Textures present; no missing external dependencies in GLB.
- No obvious broken normals, severe non-manifold artifacts, or unusable topology for the intended purpose.
- Preview visually reviewed; target-engine performance not implied without testing.
