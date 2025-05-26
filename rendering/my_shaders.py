import OpenGL.GL.shaders as shaders
from OpenGL.GL import *

# PBR-style vertex and fragment shaders (GLSL 330 core)
VERTEX_SHADER_SRC = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;

out vec3 FragPos;  // World space position
out vec3 Normal;   // World space normal

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    // Transform position to world space
    FragPos = vec3(model * vec4(aPos, 1.0));
    
    // Transform normal to world space
    Normal = mat3(transpose(inverse(model))) * aNormal;
    Normal = normalize(Normal);
    
    // Transform to clip space for rendering (apply view for camera perspective)
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core
out vec4 FragColor;

in vec3 FragPos;  // World space position
in vec3 Normal;   // World space normal

struct DirectionalLight {
    vec3 direction;  // World space direction
    vec3 color;
    float intensity;
};

uniform vec3 viewPos;  // World space camera position
uniform vec3 baseColor;
uniform vec3 emissiveColor;
uniform float metallic;
uniform float roughness;
uniform float specular;

uniform DirectionalLight dirLight;

const float PI = 3.14159265359;

// PBR functions
float DistributionGGX(vec3 N, vec3 H, float roughness)
{
    float a = roughness*roughness;
    float a2 = a*a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;

    float nom   = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return nom / denom;
}

float GeometrySchlickGGX(float NdotV, float roughness)
{
    float r = (roughness + 1.0);
    float k = (r*r) / 8.0;

    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return nom / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);

    return ggx1 * ggx2;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

void main()
{
    // World space vectors
    vec3 N = normalize(Normal);
    vec3 V = normalize(viewPos - FragPos);
    vec3 L = normalize(-dirLight.direction);
    vec3 H = normalize(V + L);
    
    // Calculate reflectance at normal incidence
    vec3 F0 = vec3(0.04); 
    F0 = mix(F0, baseColor, metallic);
    
    // Cook-Torrance BRDF
    float NDF = DistributionGGX(N, H, roughness);   
    float G   = GeometrySmith(N, V, L, roughness);      
    vec3 F    = fresnelSchlick(max(dot(H, V), 0.0), F0);
           
    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - metallic;
    
    vec3 numerator    = NDF * G * F; 
    float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.0001;
    vec3 specular = numerator / denominator;
    
    // Add to outgoing radiance Lo
    float NdotL = max(dot(N, L), 0.0);        
    vec3 Lo = (kD * baseColor / PI + specular) * dirLight.color * dirLight.intensity * NdotL;
    
    // Ambient lighting
    vec3 ambient = vec3(0.03) * baseColor;
    
    // Add emissive
    vec3 emissive = emissiveColor;
    
    // Final color
    vec3 color = ambient + Lo + emissive;
    
    // HDR tonemapping
    color = color / (color + vec3(1.0));
    
    // Gamma correction
    color = pow(color, vec3(1.0/2.2));
    
    FragColor = vec4(color, 1.0);
}
"""

SKY_VERTEX_SHADER_SRC = """
#version 330 core
layout(location = 0) in vec3 aPos;
out vec3 WorldDir;

uniform mat4 projection;
uniform mat4 view;

void main() {
    WorldDir = normalize(aPos);  // Normalize for proper sphere mapping
    vec4 pos = projection * view * vec4(aPos, 1.0);
    gl_Position = pos.xyww;  // Force z to be 1.0 (furthest depth)
}
"""

SKY_FRAGMENT_SHADER_SRC = """
#version 330 core
in vec3 WorldDir;
out vec4 FragColor;

uniform sampler2D hdrTexture;
uniform float skyBrightness;

vec2 equirectangularUV(vec3 dir) {
    float u = 0.5 + atan(dir.z, dir.x) / (2.0 * 3.14159);
    float v = 0.5 - asin(dir.y) / 3.14159;
    return vec2(u, v);
}

void main() {
    vec3 dir = normalize(WorldDir);
    vec2 uv = equirectangularUV(dir);
    vec3 color = texture(hdrTexture, uv).rgb;
    color *= skyBrightness;
    FragColor = vec4(color, 1.0);
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