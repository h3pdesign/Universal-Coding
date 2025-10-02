import bpy
import bmesh

# Load heightmap (update path to your downloaded .hgt file converted to PNG)
img = bpy.data.images.load("/path/to/N00E000.SRTMGL1.png")  # Convert .hgt to PNG first

# Add subdivided plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
plane = bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=100)  # High detail
bpy.ops.object.mode_set(mode='OBJECT')

# Displace by heightmap
mat = bpy.data.materials.new(name="TerrainMat")
plane.data.materials.append(mat)
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = img
mat.node_tree.links.new(bsdf.inputs['Alpha'], tex.outputs['Color'])  # Displacement

# Render settings
bpy.context.scene.render.filepath = "/path/to/output.png"
bpy.ops.render.render(write_still=True)