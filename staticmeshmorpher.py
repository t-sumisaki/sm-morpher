bl_info = {
    "name": "StaticMeshMorpher for UnrealEngine4",
    "author": "T_Sumisaki",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "description": "StaticMeshMorpher",
    "category": "Object",
}


import bpy


class SMM_PT_pack_morph_target_panel(bpy.types.Panel):
    """ Pack morph target panel """

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SMM"
    bl_label = "StaticMesh Morpher"
    bl_idname = "SMM_PT_pack_morph_target"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.label(text="Original Object: ")
        row = layout.row(align=True)
        row.prop(scene, "smm_original_mesh", text="")

        layout.label(text="MorphTarget1: ")
        row = layout.row(align=True)
        row.prop(scene, "smm_morph_target_one", text="")

        if scene.smm_morph_target_one is not None:
            layout.label(text="MorphTarget2: ")
            row = layout.row(align=True)
            row.prop(scene, "smm_morph_target_two", text="")

        row = layout.row(align=True)
        row.prop(scene, "smm_store_morph1_normals")

        row = layout.row(align=True)
        row.prop(scene, "smm_store_object_pivot_location")

        row = layout.row(align=True)

        col = layout.column(align=True)
        col.operator("smm.pack_morph_target", text="Pack MorphTarget")


class SMM_OT_pack_morph_target(bpy.types.Operator):
    """ Pack morphtarget operation """

    bl_idname = "smm.pack_morph_target"
    bl_label = "Pack morph target"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.scene.smm_original_mesh is not None
            and context.scene.smm_morph_target_one is not None
        )

    def execute(self, context):

        two_morph = False

        obj_original_mesh = context.scene.smm_original_mesh
        obj_morph_target_one = context.scene.smm_morph_target_one
        obj_morph_target_two = context.scene.smm_morph_target_two

        original_mesh: bpy.types.Mesh = None
        morph_target_one_mesh: bpy.types.Mesh = None
        morph_target_two_mesh: bpy.types.Mesh = None

        store_pivot_location = context.scene.smm_store_object_pivot_location
        store_morph1_normal = context.scene.smm_store_morph1_normals

        if obj_original_mesh is None:
            self.report({"ERROR"}, "Choose Original Mesh")
            return {"FINISHED"}
        if not is_mesh(obj_original_mesh):
            self.report({"ERROR"}, "Choose Original Mesh")
            return {"FINISHED"}

        if obj_morph_target_one is None:
            self.report({"ERROR"}, "Choose MorphTarget mesh")
            return {"FINISHED"}
        if not is_mesh(obj_morph_target_one):
            self.report({"ERROR"}, "Choose MorphTarget mesh (Target1)")
            return {"FINISHED"}

        if obj_morph_target_two is not None:
            if not is_mesh(obj_morph_target_two):
                self.report({"ERROR"}, "Choose MorphTarget mesh (Target2)")
                return {"FINISHED"}
            print("Use second morph")
            two_morph = True

        original_mesh = context.scene.smm_original_mesh.data
        morph_target_one_mesh = context.scene.smm_morph_target_one.data
        if two_morph:
            morph_target_two_mesh = context.scene.smm_morph_target_two.data

        if not compare_vert_counts(original_mesh, morph_target_one_mesh):
            self.report({"ERROR"}, "Vertices count is not match. (Target1)")
            return {"FINISHED"}

        if two_morph and not compare_vert_counts(original_mesh, morph_target_two_mesh):
            self.report({"ERROR"}, "Vertices count is not match. (Target2)")
            return {"FINISHED"}

        num_of_verts = get_num_of_verts(original_mesh)
        buffer0 = [[0, 0, 0]] * num_of_verts
        buffer2 = [[0, 0, 0]] * num_of_verts
        buffer3 = [[0, 0, 0]] * num_of_verts
        buffer4 = [[0, 0, 0]] * num_of_verts

        print("Processing morph targets...")
        vector_offset2 = [0, 0, 0]

        if store_pivot_location:
            origin_mesh_pivot_pos = obj_original_mesh.location * 255
            for i in range(num_of_verts):
                buffer2[i] = [
                    origin_mesh_pivot_pos[0],
                    255 - origin_mesh_pivot_pos[1],
                    0,
                ]
            vector_offset2 = origin_mesh_pivot_pos

        for i in range(num_of_verts):

            origin_vert_pos = get_vertex_co(original_mesh, i)
            target_vert_pos1 = get_vertex_co(morph_target_one_mesh, i)

            if two_morph:
                target_vert_pos2 = get_vertex_co(morph_target_two_mesh, i)
                vector_offset2 = (target_vert_pos2 - origin_vert_pos)

            vector_offset1 = (target_vert_pos1 - origin_vert_pos)
            new_normal1 = get_vertex_normal(morph_target_one_mesh, i)
            new_normal1 = arrmul(new_normal1, (1.0, -1.0, 1.0))
            new_normal1 = arrmul(arradd(new_normal1, 1.0), 0.5)
            # new_normal1 = arrmul(new_normal1, 255.0)

            print(f'VO2: {vector_offset2}')
            print(f'VO1: {vector_offset1}')
            print(f'NOR: {new_normal1}')
            if store_morph1_normal:
                buffer0[i] = new_normal1

            if two_morph:
                buffer2[i] = [vector_offset2[0], (1.0 - (vector_offset2[1] * -1)), 0]

            buffer3[i] = [vector_offset2[2], (1.0 - vector_offset1[1]), 0]
            buffer4[i] = [(vector_offset2[2] * -1), (1.0 - vector_offset1[2]), 0]

        if store_morph1_normal:
            apply_vertex_color(original_mesh, 0, buffer0)

        if two_morph:
            apply_uv_channel(original_mesh, 1, buffer2)

        apply_uv_channel(original_mesh, 2, buffer3)
        apply_uv_channel(original_mesh, 3, buffer4)

        return {"FINISHED"}


def arrmul(arr, other):
    if type(other) in (int, float):
        return [v * other for v in arr]

    return [v * o for v, o in zip(arr, other)]


def arradd(arr, other):
    if type(other) in (int, float):
        return [v + other for v in arr]

    return [v + o for v, o in zip(arr, other)]


def is_mesh(obj: bpy.types.Object) -> bool:
    return obj.type == "MESH"


def compare_vert_counts(base: bpy.types.Mesh, other: bpy.types.Mesh) -> bool:
    return len(base.vertices) == len(other.vertices)


def get_num_of_verts(mesh: bpy.types.Mesh) -> int:
    return len(mesh.vertices)


def get_vertex_co(mesh: bpy.types.Mesh, index: int) -> list:
    return mesh.vertices[index].co


def get_vertex_normal(mesh: bpy.types.Mesh, index: int) -> list:
    return mesh.vertices[index].normal


def apply_vertex_color(mesh: bpy.types.Mesh, index: int, color: list):

    layer = None
    layer_name = f'Col_{index}'

    print(f'Apply vertex color -> {layer_name}')

    layer = mesh.vertex_colors.get(layer_name)

    if layer is None:
        layer = mesh.vertex_colors.new(name=layer_name)
    
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_vert_index = mesh.loops[loop_index].vertex_index
            layer.data[loop_index].color = fillto4(color[loop_vert_index])

def apply_uv_channel(mesh: bpy.types.Mesh, index: int, data: list):

    layer = None
    layer_name = f'UVMap_{index}'


    layer = mesh.uv_layers.get(layer_name)
    if layer is None:
        layer = mesh.uv_layers.new(name=layer_name)
    
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_vert_index = mesh.loops[loop_index].vertex_index
            layer.data[loop_index].uv = data[loop_vert_index][:2]






def fillto4(arr):

    d = arr[:]
    if len(d) != 4:
        d.extend([0, 0, 0, 0])
        d = d[:4]

    return d

def normalize(v, threashold=255.0):
    return v / threashold

classes = (SMM_OT_pack_morph_target, SMM_PT_pack_morph_target_panel)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.smm_original_mesh = bpy.props.PointerProperty(
        type=bpy.types.Object, name="OriginalMesh"
    )
    bpy.types.Scene.smm_morph_target_one = bpy.props.PointerProperty(
        type=bpy.types.Object, name="MorphTarget1"
    )
    bpy.types.Scene.smm_morph_target_two = bpy.props.PointerProperty(
        type=bpy.types.Object, name="MorphTarget2"
    )
    bpy.types.Scene.smm_store_morph1_normals = bpy.props.BoolProperty(
        name="Store Morph1 Normals"
    )
    bpy.types.Scene.smm_store_object_pivot_location = bpy.props.BoolProperty(
        name="Store Pivot Location"
    )


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.smm_original_mesh
    del bpy.types.Scene.smm_morph_target_one
    del bpy.types.Scene.smm_morph_target_two
    del bpy.types.Scene.smm_store_morph1_normals
    del bpy.types.Scene.smm_store_object_pivot_location
