# DUCK HUNT - Versión Python Completa

Juego de caza de patos reimplementado en **Python con Pygame**. Versión completa y funcional con todas las características incluidas: múltiples criaturas simultáneas, animaciones de jefe, sistema de rankings persistente, modo clásico y futurista con visión por computadora.

## 🎮 Características Principales

### Mecánicas de Juego
- **Rondas Infinitas**: Juego continuo hasta Game Over
- **Múltiples Criaturas Simultáneas**:
  - Nivel 1-4: 1 criatura
  - Nivel 5-9: 2 criaturas simultáneas en posiciones aleatorias
  - Nivel 10+: 3 criaturas simultáneas
- **Sistema de Tiros Limitados**: 3 disparos por criatura principal
- **Puntuación Escalonada**:
  - 1er disparo: 3 puntos
  - 2do disparo: 2 puntos  
  - 3er disparo: 1 punto
  - Criaturas bonus (extra): 75 puntos c/u
- **Bonificación por Rondas**: Ronda × 10 puntos al completar
- **Dificultad Progresiva**: Velocidad aumenta cada ronda
- **Animación de Jefe**: Cada 3 muertes aparece el "asesino" de la criatura con secuencia de entrada/salida (2.5s de pausa post-jefe)

### Modos de Juego
- **Clásico**: Dispara con click izquierdo del ratón
- **Futurista**: Puntería con la mano via cámara + cierre de puño para disparar (MediaPipe)

### Mapas Disponibles
- Clásico
- Arcade
- Caos
- Infierno
- Plaga (con zombie duck)

### Criaturas
- Pato
- Gaviota
- Fantasma
- Murciélago
- Zombie Duck (exclusivo del mapa Plaga)

### 📊 Sistema de Rankings
- Rankings persistentes guardados en JSON
- Filtro por modo de juego (Clásico / Futurista)
- Mostrar todos los modos juntos
- Top 5 historiales por combinación modo/mapa
- Almacenamiento en `data/duck_hunt_rankings.json`

### 🎨 Interfaz Gráfica
- **Menú Principal**: Jugar, Instrucciones, Rankings, Historia (video), Seleccionar Modo
- **Selector de Mapa**: Carrusel interactivo con vista previa
- **HUD de Juego**: 
  - Iconos de criaturas con estado (color = viva, silueta negra = muerta)
  - Contador de disparos
  - Puntuación en tiempo real
  - Popups de puntaje que flotan y desaparecen
- **Pantalla Game Over**: Puntuación final, ronda, botones interactivos
- **Pantalla de Rankings**: Tablas por filtro, navegación por teclado
- **Historia**: Reproductor de video integrado (ffpyplayer)

### 🔊 Audio
- Música de fondo (adaptativa por estado)
- Sonido de disparo
- Sonidos de perro (feliz, puntuación, fallo)
- Sonidos de criaturas (quack, aleteo)
- Sonido de puntuación y bonus

### 🎮 Controles
| Acción | Clásico | Futurista |
|--------|---------|-----------|
| Disparar | Click izquierdo | Cierre de puño |
| Apuntar | Ratón | Mano por cámara |
| Pantalla Completa | F11 | F11 |
| Instrucciones | Click en menú | Click en menú |
| Rankings | Click en menú | Click en menú |
| Navegar Rankings | ←/→/Tab | ←/→/Tab |
| Menú | ESC | ESC |

## 📁 Estructura del Proyecto

```
Duck-Hunt/
├── pyproject.toml                    # Configuración del proyecto (uv)
├── README.md                          # Este archivo
├── assets/                            # Recursos multimedia
│   ├── images/
│   │   ├── backgrounds/              # Fondos de mapas
│   │   ├── creatures/                # Sprites de criaturas
│   │   ├── ui/                       # Elementos de interfaz
│   │   └── dog/                      # Sprites del perro
│   ├── audio/
│   │   ├── music/                    # Música de fondo
│   │   ├── sfx/                      # Efectos de sonido
│   │   └── voices/                   # Audio del perro
│   ├── fonts/                         # Tipografías personalizadas
│   ├── video/                         # Videos (historia)
│   │   └── duck-hunt-history.mp4     # Video introductorio
│   └── hand_landmarker.task          # Modelo MediaPipe para visión
├── src/duck_hunt/                     # Código fuente Python
│   ├── __init__.py
│   ├── ui_tk.py                       # Interfaz principal (Pygame)
│   ├── config.py                      # Constantes y configuración
│   ├── game_state.py                  # Lógica del juego
│   ├── storage.py                     # Persistencia (JSON)
│   ├── menu_flow.py                   # Flujo del menú
│   ├── session.py                     # Sesión de juego
│   ├── runtime.py                     # Motor de ejecución
│   ├── timing.py                      # Sistema de timers
│   ├── rng.py                         # Generador de números aleatorios
│   ├── rng_tools.py                   # Herramientas de RNG
│   ├── telemetry.py                   # Sistema de telemetría
│   ├── vision_control.py              # Control de visión (MediaPipe)
│   ├── command_adapter.py             # Adaptador de comandos
│   └── cli.py                         # Interfaz de línea de comandos
├── tests/                             # Suite de pruebas
│   ├── rng/                           # Pruebas de RNG
│   ├── game/                          # Pruebas de lógica del juego
│   ├── menu/                          # Pruebas de menú
│   ├── runtime/                       # Pruebas de runtime
│   ├── session/                       # Pruebas de sesión
│   └── storage/                       # Pruebas de almacenamiento
├── docs/                              # Documentación
│   └── RNG_CONTRACT.md               # Especificación del RNG
├── data/                              # Datos persistentes
│   └── duck_hunt_rankings.json       # Rankings guardados
└── .github/
    └── copilot-instructions.md       # Guías de desarrollo
```

## 🚀 Instalación y Ejecución

### Requisitos
- Python 3.12+
- Gestor `uv`
- Cámara web (solo para modo Futurista)

### Instalación
```bash
# Clonar y navegar al directorio
cd Duck-Hunt

# Instalar dependencias
uv sync

# (Opcional) Instalar dependencias de visión
uv sync --extra vision
```

### Ejecutar el Juego
```bash
# Interfaz gráfica (Pygame)
uv run duck-hunt-ui

# Interfaz de línea de comandos
uv run duck-hunt-cli
```

### Ejecutar Pruebas
```bash
# Todas las pruebas
uv run python -m unittest discover -s tests

# Solo pruebas de RNG
uv run python -m unittest tests.rng.test_rng_parity

# Solo pruebas de juego
uv run python -m unittest tests.game.test_game_state
```

## 🎯 Cómo Jugar

1. Ejecuta `uv run duck-hunt-ui`
2. Selecciona modo de juego (Clásico o Futurista)
3. Ingresa tu nombre
4. Selecciona un mapa del carrusel
5. ¡A cazar!
   - **Clásico**: Haz clic en las criaturas
   - **Futurista**: Apunta con la mano y cierra el puño
6. Acumula puntos y sube en los rankings
7. Cada 3 muertes aparece el jefe con una pausa de 2.5s después

## 🏆 Estrategia
- Dispara rápido para maximizar puntos (3 en primer tiro)
- Las rondas posteriores dan bonificaciones más grandes
- Estudia el patrón de movimiento para anticipar
- Con múltiples criaturas, prioriza las más cercanas al borde

## 🔧 Dependencias Principales
- **Pygame**: Renderizado gráfico
- **Pillow**: Procesamiento de imágenes
- **MediaPipe**: Detección de manos (modo Futurista)
- **OpenCV**: Captura de cámara
- **ffpyplayer**: Reproducción de videos
- **uv**: Gestor de dependencias

## 📊 Arquitectura
- **Determinismo**: RNG independiente con seeds reproducibles
- **Separación de Capas**: Config → Storage → Menu → Session → Runtime → UI
- **Event-Driven**: Sistema de eventos para comunicación
- **Persistencia**: Rankings guardados automáticamente en JSON
- **Telemetría**: Logging opcional de eventos del juego

## ✅ Estado del Proyecto
- ✨ **COMPLETO**: Todas las características implementadas
- ✅ Juego principal funcional
- ✅ Sistema de rankings
- ✅ Múltiples criaturas simultáneas
- ✅ Animaciones de jefe
- ✅ Modo de visión por computadora
- ✅ Sistema de audio completo
- ✅ 42/42 pruebas pasando

## 📝 Notas Técnicas
- Resolución: 1280×720
- FPS: 60 (objetivo)
- El juego usa un RNG con seeds explícitas para determinismo
- Audio bloqueado hasta primera interacción del usuario (restricción de navegador/SO)
- Fallback automático a modo Clásico si no se detecta cámara en Futurista

## 📄 Licencia
Proyecto educativo - Libre para usar, modificar y distribuir

---

**Versión**: 3.0 - Versión Python
**Última Actualización**: Abril 2026  
