# DUCK HUNT - Versión Remasterizada

Un videojuego de caza de patos moderno con arquitectura profesional, sistema de menú, rankings persistentes y mecánicas de juego mejoradas.

## Características

### 🎮 Mecánicas de Juego
- **Rondas Infinitas**: El juego continúa indefinidamente hasta que pierdes
- **Un Pato a la Vez**: Solo aparece un pato en pantalla, el siguiente aparece al eliminar el anterior
- **Sistema de Tiros Limitados**: Tienes 3 tiros para eliminar cada pato
- **Sistema de Puntuación Escalonada**:
  - 1er tiro: 3 puntos
  - 2do tiro: 2 puntos
  - 3er tiro: 1 punto
- **Bonificación por Rondas**:
  - Ronda 1: +10 puntos
  - Ronda 2: +20 puntos
  - Ronda 3: +30 puntos (y así sucesivamente)
- **Dificultad Progresiva**: La velocidad de los patos aumenta con cada ronda
- **Sistema de Vidas**: Si fallas los 3 tiros, Game Over

### 📊 Sistema de Rankings
- Rankings persistentes guardados en localStorage
- Vista de top puntuaciones con información de rondas alcanzadas
- Historial de partidas con fechas

### 🎨 Interfaz
- **Menú Principal**: Opciones de Jugar, Rankings, Salir
- **HUD de Juego**: Muestra puntuación, ronda actual y tiros disponibles
- **Pantalla Game Over**: Muestra puntuación final y ronda alcanzada
- **Interfaz Intuitiva**: Diseño accesible y responsivo

### 🔊 Audio
- Sonido de disparo
- Sonido de perro feliz
- Sonidos de patos (quack, aleteo)
- Sonido de puntuación

## 📁 Estructura del Proyecto

```
duck-hunt-master/
├── index.html                          # Archivo principal HTML
├── pyproject.toml                      # Configuración del proyecto Python (uv)
├── Duck_Hunt_LCG_Analysis.ipynb        # Notebook educativo: Análisis de PRNG LCG
├── execute_notebook_style.py           # Script ejecutable del análisis educativo
├── assets/                             # Archivos multimedia
│   ├── images/                        # Imágenes (sprites, fondos)
│   ├── audio/                         # Archivos de audio
│   └── fonts/                         # Fuentes personalizadas
├── src/                                # Código fuente
│   ├── js/                            # Archivos JavaScript
│   │   ├── config.js                 # Configuración del juego
│   │   ├── storage.js                # Sistema de almacenamiento
│   │   ├── menu.js                   # Lógica del menú
│   │   ├── game.js                   # Lógica principal del juego
│   │   └── main.js                   # Archivo de inicialización
│   ├── css/                           # Hojas de estilo
│   │   ├── main.css                  # Estilos generales
│   │   ├── menu.css                  # Estilos del menú
│   │   ├── game.css                  # Estilos del juego
│   │   └── rankings.css              # Estilos de rankings
│   └── duck_hunt/                     # Módulos Python
│       ├── __init__.py               # Inicializador del paquete
│       ├── rng.py                    # Generador de números aleatorios base
│       ├── prng_lcg.py               # Implementación de LCG (Congruencias Lineales)
│       ├── config.py                 # Configuración del juego (Python)
│       ├── game_state.py             # Estado del juego
│       ├── menu_flow.py              # Flujo del menú
│       ├── runtime.py                # Motor de ejecución
│       └── ui_tk.py                  # Interfaz gráfica (Tkinter)
├── tests/                              # Pruebas unitarias
│   ├── rng/                           # Pruebas de PRNG
│   │   └── test_rng_parity.py        # Validación de paridad JS/Python
│   ├── game/                          # Pruebas de lógica de juego
│   ├── menu/                          # Pruebas de flujo de menú
│   └── ...
├── docs/                               # Documentación
│   └── RNG_CONTRACT.md                # Especificación del contrato PRNG
├── data/                               # Datos persistentes
│   └── duck_hunt_rankings.json        # Rankings guardados
└── README.md                           # Este archivo
```

## 🚀 Cómo Jugar

1. Abre `index.html` en tu navegador
2. Haz clic en "JUGAR" para iniciar
3. Dispara a los patos haciendo clic en ellos
4. Acumula puntos según la estrategia: primer tiro = mas puntos
5. Evita fallar 3 tiros seguidos (Game Over)
6. Observa cómo aumenta la dificultad cada ronda
7. Ve tu puntuación final y compárala en los RANKINGS

## 💾 Almacenamiento

- Los rankings se guardan automáticamente en el localStorage del navegador
- Tu historial se mantiene entre sesiones
- Los datos se pierden solo si limpias el almacenamiento local

## 🎯 Estrategia

- Enfócate en eliminar al pato rápido para obtener 3 puntos
- Las rondas posteriores dan bonificaciones más grandes
- La velocidad aumenta progresivamente - ¡anticipa el movimiento!
- No influye cuántos tiros uses para los puntos de ronda

## 🛠️ Uso de Tecnologías

- **HTML5**: Estructura y semántica
- **CSS3**: Estilos modernos con gradientes y animaciones
- **JavaScript Vanilla**: Sin dependencias externas
- **LocalStorage**: Persistencia de datos

## 🐍 Migración Python (uv)

La migración gradual a Python usa `uv` como gestor de entorno/dependencias.

### Componentes Implementados

- **PRNG LCG (Congruencias Lineales)**: `src/duck_hunt/prng_lcg.py`
  - Algoritmo: $X_{n+1} = (a \times X_n + c) \bmod m$
  - Parámetros: a=1103515245, c=12345, m=2^32 (estándar glibc)
  - Período: 2^32 = 4,294,967,296

- **Configuración del Juego**: `src/duck_hunt/config.py`
- **Estado del Juego**: `src/duck_hunt/game_state.py`
- **Flujo de Menú**: `src/duck_hunt/menu_flow.py`
- **Motor de Ejecución**: `src/duck_hunt/runtime.py`
- **Interfaz Gráfica**: `src/duck_hunt/ui_tk.py` (Tkinter)

### Análisis Educativo

**Nuevo**: Notebook interactivo y análisis completo del PRNG LCG

```bash
# Ver análisis completo en formato educativo
uv run python execute_notebook_style.py

# Abrir notebook en Jupyter/VS Code
# Duck_Hunt_LCG_Analysis.ipynb
```

El notebook incluye:
- Explicación matemática del LCG
- Generación de números aleatorios [0.0, 1.0)
- Simulación de selección de mapas
- Comparación 16-bits vs 32-bits
- Simulación de partida completa
- Verificación de reproducibilidad
- Integración en el sistema del juego

### Comandos Python

```bash
# Instalar dependencias
uv sync

# Ejecutar juego completo
uv run python -m duck_hunt

# Ejecutar análisis educativo
uv run python execute_notebook_style.py

# Validar paridad RNG JS/Python
uv run python -m unittest tests.rng.test_rng_parity

# Ejecutar todas las pruebas
uv run python -m unittest discover
```

### Estrategia de Migración

1. ✅ **Fase 1**: PRNG LCG independiente y validación de paridad
2. 🔄 **Fase 2**: Portabilidad de config y almacenamiento
3. 🔄 **Fase 3**: Flujo de menú e interfaz
4. 🔄 **Fase 4**: Lógica de juego completa
5. 🔄 **Fase 5**: Visión computacional (opcional)

## � Recursos Educativos

### PRNG LCG (Generador de Congruencias Lineales)

- **Notebook Interactivo**: [Duck_Hunt_LCG_Analysis.ipynb](Duck_Hunt_LCG_Analysis.ipynb)
- **Script Ejecutable**: `execute_notebook_style.py`
- **Especificación**: [docs/RNG_CONTRACT.md](docs/RNG_CONTRACT.md)

Estos recursos documentan:
- La implementación del LCG en Python
- Parámetros estándar (glibc)
- Validación de reproducibilidad
- Comparación de períodos (16-bits vs 32-bits)
- Integración en mecánicas del juego

### Pruebas de Paridad

El proyecto valida que las secuencias JavaScript y Python sean idénticas:

```bash
uv run python -m unittest tests.rng.test_rng_parity
```

Esto asegura que la migración mantenga el comportamiento determinista del juego.

## 📝 Notas

- El juego utiliza recursos gráficos de alta calidad
- Optimizado para navegadores modernos
- Responsive: funciona en desktop y dispositivos móviles
- **Nuevo**: PRNG completamente analizado y documentado con fines educativos
- **Nuevo**: Notebook de modelamiento matemático del generador aleatorio

## 📄 Licencia

Proyecto educativo - Libre para usar y modificar

---

**Versión**: 2.1 - Con Análisis Educativo de PRNG LCG  
**Última Actualización**: Abril 2026  
**Cambios Recientes**: 
- ✨ Notebook educativo de Congruencias Lineales (LCG)
- 📊 Script de análisis con simulaciones completas
- 🔍 Validación de paridad RNG JS/Python
- 📈 Documentación de integración en el sistema del juego
