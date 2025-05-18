# Recent Changes

- **[INSTRUCTION FOR AI]**: Only list the last 10 changes in this section. Always use a first-in, last-out (FILO) approach: the most recent change is at the top; process changes from newest to oldest. When adding a new change, remove the oldest if there are more than 10.
- Migrated the editor UI to PySide6/Qt, replacing the old OpenGL/GLFW and custom container-based UI. The editor now uses a QMainWindow with dockable panels and a QOpenGLWidget for the viewport.
- Removed all references to VerticalBox, HorizontalBox, and EditorTopBar from the codebase. The new UI is fully Qt-based.

# AI_readme

## Current State
- Modular editor renderer inspired by Unreal/Unity, using OpenGL and GLFW in Python.
- UI layout with menu bar, toolbar, left (scene hierarchy), right (properties), and bottom (content browser) panels, all flush with window edges.
- Central 3D viewport for scene rendering, resizes dynamically with the window.
- Scene hierarchy panel lists entities in the world.
- Properties panel shows details of the selected entity.
- Content browser panel displays files/folders from the assets directory.
- Gizmo system for moving objects in the viewport.
- Raycasting for selecting objects in the scene.
- All UI and viewport layout is responsive to window resizing.

## Short-Term Goals
- Add interactivity to panels (e.g., selecting entities from the hierarchy, clicking files in the content browser).
- Implement drag-and-drop from the content browser to the viewport.
- Add more tools (rotate, scale) to the gizmo system.
- Improve visual feedback (hover, selection highlights, icons).
- Add support for loading/saving scenes.

## Long-Term Goals
- Full-featured 3D editor with modular, extensible UI.
- Support for custom assets, prefabs, and scripting.
- Advanced scene management (hierarchies, parenting, grouping).
- In-editor asset import and preview.
- Undo/redo, copy/paste, and multi-object selection.
- Export to game runtime or other engines.
- Polished, professional user experience similar to Unreal/Unity editors. 