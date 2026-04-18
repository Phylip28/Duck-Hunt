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
├── index.html                 # Archivo principal HTML
├── assets/                    # Archivos multimedia
│   ├── images/               # Imágenes (sprites, fondos)
│   ├── audio/                # Archivos de audio
│   └── fonts/                # Fuentes personalizadas
├── src/                       # Código fuente
│   ├── js/                   # Archivos JavaScript
│   │   ├── config.js         # Configuración del juego
│   │   ├── storage.js        # Sistema de almacenamiento
│   │   ├── menu.js           # Lógica del menú
│   │   ├── game.js           # Lógica principal del juego
│   │   └── main.js           # Archivo de inicialización
│   └── css/                  # Hojas de estilo
│       ├── main.css          # Estilos generales
│       ├── menu.css          # Estilos del menú
│       ├── game.css          # Estilos del juego
│       └── rankings.css      # Estilos de rankings
└── README.md                 # Este archivo
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

## 📝 Notas

- El juego utiliza recursos gráficos de alta calidad
- Optimizado para navegadores modernos
- Responsive: funciona en desktop y dispositivos móviles

## 📄 Licencia

Proyecto educativo - Libre para usar y modificar

---

**Versión**: 2.0 Remasterizada  
**Última Actualización**: Abril 2026
