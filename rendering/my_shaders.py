import OpenGL.GL.shaders as shaders
from OpenGL.GL import *


# PBR-style vertex and fragment shaders (GLSL 330 core)
VERTEX_SHADER_SRC = """
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;

out vec3 FragPos;
out vec3 Normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core

struct DirectionalLight {
    vec3 direction;
    vec3 color;
    float intensity;
};

uniform DirectionalLight dirLight;

in vec3 FragPos;
in vec3 Normal;

out vec4 FragColor;

uniform vec3 baseColor;
uniform vec3 emissiveColor;
uniform float metallic;
uniform float roughness;
uniform float specular;

uniform vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
uniform vec3 viewPos;

void main() {
    vec3 normal = normalize(Normal);
    vec3 lightDir = normalize(-dirLight.direction);
    float diff = max(dot(normal, lightDir), 0.0);

    vec3 diffuse = diff * dirLight.color * dirLight.intensity;
    vec3 ambient = vec3(0.05) * dirLight.color;

    vec3 finalColor = (ambient + diffuse) * baseColor;
    FragColor = vec4(finalColor, 1.0);
}
"""

SKYBOX_VERTEX_SHADER_SRC = """
#version 330 core
layout(location = 0) in vec3 aPos;
out vec3 TexCoords;

uniform mat4 view;
uniform mat4 projection;

void main() {
    TexCoords = aPos;
    vec4 pos = projection * view * vec4(aPos, 1.0);
    gl_Position = pos.xyww;
}
"""

SKYBOX_FRAGMENT_SHADER_SRC = """
#version 330 core
in vec3 TexCoords;
out vec4 FragColor;

uniform samplerCube skybox;

void main() {
    FragColor = texture(skybox, TexCoords);
}
"""

def compile_shader_program(vertex_src=VERTEX_SHADER_SRC, fragment_src=FRAGMENT_SHADER_SRC):
    vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
    fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
    return shaders.compileProgram(vertex_shader, fragment_shader)


class Material:
    def __init__(self,
                 base_color=(1.0, 1.0, 1.0),
                 metallic=0.0,
                 roughness=0.5,
                 specular=0.5,
                 emissive_color=(0.0, 0.0, 0.0),
                 normal_map=None,
                 ao_map=None,
                 base_color_map=None):
        self.base_color = base_color
        self.metallic = metallic
        self.roughness = roughness
        self.specular = specular
        self.emissive_color = emissive_color
        self.normal_map = normal_map
        self.ao_map = ao_map
        self.base_color_map = base_color_map