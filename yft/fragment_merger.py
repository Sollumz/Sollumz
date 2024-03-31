from typing import Optional

from ..cwxml.drawable import Geometry, Shader
from ..cwxml.fragment import Fragment, PhysicsChild


def get_all_frag_geoms(frag_xml: Fragment) -> list[Geometry]:
    """Get all Geometries in a Fragment including those in Physics children and Cloths drawables."""
    geoms = frag_xml.drawable.all_geoms

    for child in frag_xml.physics.lod1.children:
        geoms.extend(child.drawable.all_geoms)

    for cloth in frag_xml.cloths:
        geoms.extend(cloth.drawable.all_geoms)

    return geoms


class FragmentMerger:
    """Merge hi and non hi Fragments."""
    @property
    def phys_children(self) -> list[PhysicsChild]:
        return self.frag.physics.lod1.children

    @property
    def phys_children_hi(self) -> list[PhysicsChild]:
        return self.hi_frag.physics.lod1.children

    def __init__(self, frag: Fragment, hi_frag: Fragment) -> None:
        self.frag = frag
        self.hi_frag = hi_frag

        if len(self.phys_children) != len(self.phys_children_hi):
            raise ValueError(
                f"Cannot merge Fragments '{self.frag.name}' and '{self.hi_frag.name}': Both Fragments must have same number of children!")

    def merge(self) -> Fragment:
        shaders: list[Shader] = self.frag.drawable.shader_group.shaders
        hi_shaders: list[Shader] = self.hi_frag.drawable.shader_group.shaders

        shader_merger = FragShaderMerger(shaders, hi_shaders)
        merged_shaders = shader_merger.merge()

        self.frag.drawable.shader_group.shaders = merged_shaders

        shader_merger.update_geom_shader_inds(self.frag)
        shader_merger.update_hi_geom_shader_inds(self.hi_frag)

        self.frag.drawable.hi_models = self.hi_frag.drawable.drawable_models_high

        self.merge_hi_children()

        # NOTE: we don't merge Cloth drawables because they have the same mesh in hi and non-hi fragments

        return self.frag

    def merge_hi_children(self):
        """Merge the hi and non hi Drawables of each physics child."""
        for child, hi_child in zip(self.phys_children, self.phys_children_hi):
            drawable = child.drawable
            hi_drawable = hi_child.drawable

            if drawable.is_empty or hi_drawable.is_empty:
                continue

            drawable.hi_models = hi_drawable.drawable_models_high


class FragShaderMerger:
    """Merge shader groups of Fragment and hi Fragment."""

    @property
    def shaders_left_to_merge(self):
        return self._shader_ind < len(self.shaders)

    @property
    def hi_shaders_left_to_merge(self):
        return self._hi_shader_ind < len(self.hi_shaders)

    @property
    def current_shader(self) -> Optional[Shader]:
        if not self.shaders_left_to_merge:
            return None

        return self.shaders[self._shader_ind]

    @property
    def current_hi_shader(self) -> Optional[Shader]:
        if not self.hi_shaders_left_to_merge:
            return None

        return self.hi_shaders[self._hi_shader_ind]

    def __init__(self, shaders: list[Shader], hi_shaders: list[Shader]) -> None:
        self.shaders = shaders
        self.hi_shaders = hi_shaders

        self.new_shader_inds: dict[int, int] = {}
        self.new_hi_shader_inds: dict[int, int] = {}
        self.merged_shaders: list[Shader] = []

        self._shader_ind: int = 0
        self._hi_shader_ind: int = 0

    def merge(self):
        """Merge _hi.yft shader group into non hi shader group. Returns the merged shaders."""
        while self.shaders_left_to_merge or self.hi_shaders_left_to_merge:
            if self.hi_shaders_left_to_merge and not self.shaders_left_to_merge:
                self._add_hi_shader()
                continue
            elif self.shaders_left_to_merge and not self.hi_shaders_left_to_merge:
                self._add_shader()
                continue

            if self.current_shader == self.current_hi_shader:
                # Doesn't matter if we add the hi shader or non hi if they are both the same
                self._add_hi_shader()
                self._update_shader_ind()
                continue

            if self.current_shader not in self.hi_shaders:
                self._add_shader()
                continue

            if self.current_hi_shader not in self.shaders:
                self._add_hi_shader()
                continue

            self._add_hi_shader()

        return self.merged_shaders

    def _add_shader(self):
        shader = self.shaders[self._shader_ind]

        self.merged_shaders.append(shader)
        self._update_shader_ind()

    def _update_shader_ind(self):
        self.new_shader_inds[self._shader_ind] = len(self.merged_shaders) - 1
        self._shader_ind += 1

    def _add_hi_shader(self):
        shader = self.hi_shaders[self._hi_shader_ind]

        self.merged_shaders.append(shader)
        self._update_hi_shader_ind()

    def _update_hi_shader_ind(self):
        self.new_hi_shader_inds[self._hi_shader_ind] = len(
            self.merged_shaders) - 1
        self._hi_shader_ind += 1

    def update_geom_shader_inds(self, frag: Fragment):
        """Update shader indices in non hi Fragment to use indices from merged
        shader list."""
        geoms = get_all_frag_geoms(frag)

        for geom in geoms:
            geom.shader_index = self.new_shader_inds[geom.shader_index]

    def update_hi_geom_shader_inds(self, hi_frag: Fragment):
        """Update shader indices in hi Fragment to use indices from merged
        shader list."""
        geoms = get_all_frag_geoms(hi_frag)

        for geom in geoms:
            geom.shader_index = self.new_hi_shader_inds[geom.shader_index]
