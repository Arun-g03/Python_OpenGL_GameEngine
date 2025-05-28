import math
import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44, Vector3
from rendering.my_shaders import SKY_VERTEX_SHADER_SRC, SKY_FRAGMENT_SHADER_SRC, compile_shader_program, Material


from PIL import Image
import cv2
import weakref
    

class Rasteriser:
    def __init__(self):
        self.shader_program = compile_shader_program()
        self.cube_vao, self.vertex_count = self.create_cube_geometry()
        self.sphere_vao, self.sphere_vertex_count = self.create_sphere_geometry()
        self.sky_texture = self.load_hdr_texture("assets/justSky.hdr")
        
        self.sky_shader = compile_shader_program(SKY_VERTEX_SHADER_SRC, SKY_FRAGMENT_SHADER_SRC)
        self.floor_texture = None
        self.build_floor_mesh()
        self.mesh_vao_cache = weakref.WeakKeyDictionary()  # Cache for mesh VAOs

    def create_cube_geometry(self):
        # Position + Normal per vertex
        data = []
        def face(p1, p2, p3, p4):
            normal = np.cross(np.subtract(p2, p1), np.subtract(p3, p1))
            normal = normal / np.linalg.norm(normal)
            data.extend(p1 + normal.tolist())
            data.extend(p2 + normal.tolist())
            data.extend(p3 + normal.tolist())
            data.extend(p1 + normal.tolist())
            data.extend(p3 + normal.tolist())
            data.extend(p4 + normal.tolist())

        face([-1,-1, 1], [ 1,-1, 1], [ 1, 1, 1], [-1, 1, 1])  # front
        face([-1,-1,-1], [-1, 1,-1], [ 1, 1,-1], [ 1,-1,-1])  # back
        face([-1,-1,-1], [-1,-1, 1], [-1, 1, 1], [-1, 1,-1])  # left
        face([ 1,-1,-1], [ 1, 1,-1], [ 1, 1, 1], [ 1,-1, 1])  # right
        face([-1, 1,-1], [-1, 1, 1], [ 1, 1, 1], [ 1, 1,-1])  # top
        face([-1,-1,-1], [ 1,-1,-1], [ 1,-1, 1], [-1,-1, 1])  # bottom

        vertices = np.array(data, dtype=np.float32)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        stride = 6 * 4  # 3 position + 3 normal
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

        glBindVertexArray(0)
        return vao, len(vertices) // 6

    def create_sphere_geometry(self, stacks=16, slices=16):
        vertices = []
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = math.sin(lat0)
            zr0 = math.cos(lat0)

            lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
            z1 = math.sin(lat1)
            zr1 = math.cos(lat1)

            for j in range(slices + 1):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)

                nx0, ny0, nz0 = x * zr0, y * zr0, z0
                nx1, ny1, nz1 = x * zr1, y * zr1, z1

                vertices.extend([nx0, ny0, nz0, nx0, ny0, nz0])
                vertices.extend([nx1, ny1, nz1, nx1, ny1, nz1])

        vertices = np.array(vertices, dtype=np.float32)
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        stride = 6 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

        glBindVertexArray(0)
        return vao, len(vertices) // 6

    def draw_cube(self, position: Vector3, size: float, view: Matrix44, projection: Matrix44, material: Material, camera_pos: Vector3):
        glUseProgram(self.shader_program)
        glBindVertexArray(self.cube_vao)

        model = Matrix44.from_translation(position) * Matrix44.from_scale([size / 2] * 3)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection.astype('float32'))
        glUniform3fv(glGetUniformLocation(self.shader_program, "viewPos"), 1, camera_pos.astype('float32'))

        glUniform3fv(glGetUniformLocation(self.shader_program, "baseColor"), 1, np.array(material.base_color, dtype=np.float32))
        glUniform3fv(glGetUniformLocation(self.shader_program, "emissiveColor"), 1, np.array(material.emissive_color, dtype=np.float32))
        glUniform1f(glGetUniformLocation(self.shader_program, "metallic"), material.metallic)
        glUniform1f(glGetUniformLocation(self.shader_program, "roughness"), material.roughness)
        glUniform1f(glGetUniformLocation(self.shader_program, "specular"), material.specular)

        glUniform3f(glGetUniformLocation(self.shader_program, "dirLight.direction"), -0.5, -1.0, -0.5)
        glUniform3f(glGetUniformLocation(self.shader_program, "dirLight.color"), 1.0, 1.0, 1.0)
        glUniform1f(glGetUniformLocation(self.shader_program, "dirLight.intensity"), 1.0)

        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.vertex_count)

        glBindVertexArray(0)
        glUseProgram(0)

    def draw_sphere(self, position: Vector3, radius: float, view: Matrix44, projection: Matrix44, material: Material, camera_pos: Vector3):
        glUseProgram(self.shader_program)
        glBindVertexArray(self.sphere_vao)

        model = Matrix44.from_translation(position) * Matrix44.from_scale([radius] * 3)
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection.astype('float32'))
        glUniform3fv(glGetUniformLocation(self.shader_program, "viewPos"), 1, camera_pos.astype('float32'))

        glUniform3fv(glGetUniformLocation(self.shader_program, "baseColor"), 1, np.array(material.base_color, dtype=np.float32))
        glUniform3fv(glGetUniformLocation(self.shader_program, "emissiveColor"), 1, np.array(material.emissive_color, dtype=np.float32))
        glUniform1f(glGetUniformLocation(self.shader_program, "metallic"), material.metallic)
        glUniform1f(glGetUniformLocation(self.shader_program, "roughness"), material.roughness)
        glUniform1f(glGetUniformLocation(self.shader_program, "specular"), material.specular)

        glUniform3f(glGetUniformLocation(self.shader_program, "dirLight.direction"), -0.5, -1.0, -0.5)
        glUniform3f(glGetUniformLocation(self.shader_program, "dirLight.color"), 1.0, 1.0, 1.0)
        glUniform1f(glGetUniformLocation(self.shader_program, "dirLight.intensity"), 1.0)

        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.sphere_vertex_count)

        glBindVertexArray(0)
        glUseProgram(0)

    def set_floor_texture(self, texture_id):
        self.floor_texture = texture_id

    def build_floor_mesh(self, width=32, depth=32, y=0.0):
        vertices = []

        # Base cube geometry (unit cube centered at origin)
        def cube_vertices(x, y, z):
            s = 0.5  # size
            positions = [
                # Front face
                [-s, -s,  s], [ s, -s,  s], [ s,  s,  s], [-s,  s,  s],
                # Back face
                [-s, -s, -s], [-s,  s, -s], [ s,  s, -s], [ s, -s, -s],
                # Left face
                [-s, -s, -s], [-s, -s,  s], [-s,  s,  s], [-s,  s, -s],
                # Right face
                [ s, -s, -s], [ s,  s, -s], [ s,  s,  s], [ s, -s,  s],
                # Top face
                [-s,  s, -s], [-s,  s,  s], [ s,  s,  s], [ s,  s, -s],
                # Bottom face
                [-s, -s, -s], [ s, -s, -s], [ s, -s,  s], [-s, -s,  s],
            ]
            normals = [
                [0, 0, 1], [0, 0, -1], [-1, 0, 0],
                [1, 0, 0], [0, 1, 0], [0, -1, 0]
            ]
            indices = [
                [0, 1, 2, 0, 2, 3],       # Front
                [4, 5, 6, 4, 6, 7],       # Back
                [8, 9,10, 8,10,11],       # Left
                [12,13,14,12,14,15],      # Right
                [16,17,18,16,18,19],      # Top
                [20,21,22,20,22,23]       # Bottom
            ]

            for i, face in enumerate(indices):
                normal = normals[i]
                for idx in face:
                    px, py, pz = positions[idx]
                    vertices.extend([px + x, py + y, pz + z] + normal)

        # Build one cube per grid tile
        for x in range(width):
            for z in range(depth):
                cube_vertices(x + 0.5, y, z + 0.5)

        vertices = np.array(vertices, dtype=np.float32)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        stride = 6 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

        glBindVertexArray(0)

        self.floor_vao = vao
        self.floor_vertex_count = len(vertices) // 6

    def draw_floor(self, view, projection, material, camera_pos):
        glUseProgram(self.shader_program)
        glBindVertexArray(self.floor_vao)

        model = Matrix44.identity()
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection.astype('float32'))
        glUniform3fv(glGetUniformLocation(self.shader_program, "viewPos"), 1, camera_pos.astype('float32'))

        glUniform3fv(glGetUniformLocation(self.shader_program, "baseColor"), 1, np.array(material.base_color, dtype=np.float32))
        glUniform3fv(glGetUniformLocation(self.shader_program, "emissiveColor"), 1, np.array(material.emissive_color, dtype=np.float32))
        glUniform1f(glGetUniformLocation(self.shader_program, "metallic"), material.metallic)
        glUniform1f(glGetUniformLocation(self.shader_program, "roughness"), material.roughness)
        glUniform1f(glGetUniformLocation(self.shader_program, "specular"), material.specular)

        glDrawArrays(GL_TRIANGLES, 0, self.floor_vertex_count)

        glBindVertexArray(0)
        glUseProgram(0)

    

    

    
    def load_hdr_texture(self, path):
        hdr_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # float32 HDR
        if hdr_image is None:
            raise RuntimeError(f"Failed to load HDR texture: {path}")

        hdr_image = cv2.cvtColor(hdr_image, cv2.COLOR_BGR2RGB)  # OpenCV loads as BGR

        height, width, _ = hdr_image.shape

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, width, height, 0,
                    GL_RGB, GL_FLOAT, hdr_image)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glBindTexture(GL_TEXTURE_2D, 0)
        print("Loaded HDR texture")
        return tex_id


    def draw_sky(self, view, projection, brightness=1):
        glUseProgram(self.sky_shader)
        glDepthMask(GL_FALSE)  # Disable depth writing
        glDisable(GL_DEPTH_TEST)  # Disable depth testing for sky

        glBindVertexArray(self.sphere_vao)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.sky_texture)
        glUniform1i(glGetUniformLocation(self.sky_shader, "hdrTexture"), 0)

        # Set the brightness uniform
        glUniform1f(glGetUniformLocation(self.sky_shader, "skyBrightness"), brightness)

        # Create view matrix without translation (sky sphere centered on camera)
        view_no_translation = view.copy()
        view_no_translation[3, :3] = 0  # Remove translation component

        # Set uniforms
        glUniformMatrix4fv(glGetUniformLocation(self.sky_shader, "view"), 1, GL_FALSE, view_no_translation.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.sky_shader, "projection"), 1, GL_FALSE, projection.astype('float32'))

        # Draw the sky sphere
        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.sphere_vertex_count)

        # Restore state
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glBindVertexArray(0)
        glUseProgram(0)

    def draw_mesh(self, mesh, position, rotation, scale, material, view, projection, camera_pos):
        # print("\n=== DRAW MESH CALLED ===")
        # print(f"Mesh info:")
        # print(f"  Vertices: {len(mesh.vertices)//3}")
        # print(f"  Indices: {len(mesh.indices)}")
        # print(f"  Normals: {len(mesh.normals)//3 if mesh.normals else 0}")
        # print(f"Transform:")
        # print(f"  Position: {position}")
        # print(f"  Rotation: {rotation}")
        # print(f"  Scale: {scale}")
        # print(f"Material:")
        # print(f"  Base color: {material.base_color}")
        # print(f"  Metallic: {material.metallic}")
        # print(f"  Roughness: {material.roughness}")

        # Cache VAO/VBO/EBO for each mesh
        if mesh not in self.mesh_vao_cache:
            print("Creating new VAO/VBO/EBO for mesh")
            vao = glGenVertexArrays(1)
            vbo = glGenBuffers(1)
            ebo = glGenBuffers(1)
            glBindVertexArray(vao)
            
            # Vertices
            vertices = np.array(mesh.vertices, dtype=np.float32)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            
            # Normals (optional)
            if mesh.normals:
                normals = np.array(mesh.normals, dtype=np.float32)
                nbo = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, nbo)
                glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
                glEnableVertexAttribArray(1)
                glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            
            # Indices
            indices = np.array(mesh.indices, dtype=np.uint32)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
            glBindVertexArray(0)
            self.mesh_vao_cache[mesh] = (vao, len(indices))
            index_count = len(indices)
            #print(f"Created new VAO: {vao} with {len(indices)} indices")
        else:
            vao, index_count = self.mesh_vao_cache[mesh]
            #print(f"Using cached VAO: {vao} with {index_count} indices")

        # Set up model matrix (world space transformation)
        model = Matrix44.identity()
        model = model @ Matrix44.from_translation(position)  # First translate to position
        model = model @ Matrix44.from_eulers(rotation)       # Then rotate around that position
        model = model @ Matrix44.from_scale(scale)           # Finally scale
        #print(f"Model matrix:\n{model}")

        glUseProgram(self.shader_program)
        glBindVertexArray(vao)

        # Set all required uniforms
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "model"), 1, GL_FALSE, model.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "view"), 1, GL_FALSE, view.astype('float32'))
        glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "projection"), 1, GL_FALSE, projection.astype('float32'))
        glUniform3fv(glGetUniformLocation(self.shader_program, "viewPos"), 1, camera_pos.astype('float32'))

        # Set material properties
        glUniform3fv(glGetUniformLocation(self.shader_program, "baseColor"), 1, np.array(material.base_color, dtype=np.float32))
        glUniform3fv(glGetUniformLocation(self.shader_program, "emissiveColor"), 1, np.array(material.emissive_color, dtype=np.float32))
        glUniform1f(glGetUniformLocation(self.shader_program, "metallic"), material.metallic)
        glUniform1f(glGetUniformLocation(self.shader_program, "roughness"), material.roughness)
        glUniform1f(glGetUniformLocation(self.shader_program, "specular"), material.specular)

        # Set lighting (in world space)
        glUniform3f(glGetUniformLocation(self.shader_program, "dirLight.direction"), -0.5, -1.0, -0.5)
        glUniform3f(glGetUniformLocation(self.shader_program, "dirLight.color"), 1.0, 1.0, 1.0)
        glUniform1f(glGetUniformLocation(self.shader_program, "dirLight.intensity"), 1.0)

        # Draw the mesh
        #print("Drawing mesh...")
        glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, None)
        
        glDisable(GL_BLEND)
        glBindVertexArray(0)
        glUseProgram(0)
        #print("=== DRAW MESH COMPLETE ===\n")
