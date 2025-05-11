import math
import numpy as np
from OpenGL.GL import *
from pyrr import Matrix44, Vector3
from rendering.my_shaders import compile_shader_program, Material

from PIL import Image

class Rasteriser:
    def __init__(self):
        self.shader_program = compile_shader_program()
        self.cube_vao, self.vertex_count = self.create_cube_geometry()
        self.sphere_vao, self.sphere_vertex_count = self.create_sphere_geometry()
        self.floor_texture = None
        self.build_floor_mesh()

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

    

    def load_cubemap(faces: list[str]) -> int:
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, texture_id)

        for i, face in enumerate(faces):
            image = Image.open(face)
            image = image.convert('RGB')
            data = image.tobytes()
            width, height = image.size
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

        return texture_id
