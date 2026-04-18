# DUCK HUNT - GUÍA RÁPIDA

## 🎮 ¿CÓMO JUGAR?

### Inicio
1. Abre `index.html` en tu navegador
2. Aparecerá el menú principal con tres opciones

### Controles
- **CLICK** en el pato = Disparo
- **CLICK** en el fondo = Fallo de disparo
- Tienes **3 tiros** por pato

### Sistema de Puntos
| Tiro | Puntos |
|------|--------|
| 1er tiro | 3 ⭐ |
| 2do tiro | 2 ⭐ |
| 3er tiro | 1 ⭐ |
| Ronda completada | 10 × Número de Ronda |

**Ejemplo:**
- Ronda 1 completada: +10 puntos
- Ronda 2 completada: +20 puntos
- Ronda 3 completada: +30 puntos

### Game Over
Pierdes si fallas los 3 tiros (3 clicks en el fondo sin herirlo)

## 🎯 ESTRATEGIA

1. **Apunta rápido** - Primer tiro = máxima puntuación (3 puntos)
2. **Anticipa movimientos** - Los patos se mueven rápido y cambian dirección
3. **Cada ronda es más difícil** - La velocidad aumenta progresivamente
4. **Rondas de bonificación** - Las rondas posteriores dan más puntos

## 📊 MENÚ

### JUGAR
- Inicia una nueva partida
- Comienza en Ronda 1 con 0 puntos

### RANKINGS
- Muestra tu top 10 de puntuaciones
- Información: Rank, Puntos, Ronda, Fecha
- Se actualiza después de cada partida

### SALIR
- Cierra el juego
- (Nota: Solo funciona en algunos navegadores)

## 🔊 SONIDOS

- 🔫 Disparo
- 🦆 Pato ganador (perro feliz)
- 💀 Game Over

## 💾 DATOS

- Tus puntuaciones se guardan automáticamente en tu navegador
- Los datos persisten entre sesiones
- Para borrar: Limpia el almacenamiento local del navegador

## 📱 COMPATIBLE CON

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Navegadores basados en Chromium

## ⚙️ CONFIGURACIÓN

Si quieres modificar la dificultad, abre `src/js/config.js`:

```javascript
// Velocidad inicial de patos (por defecto: 5)
initialDuckSpeed: 5,

// Incremento de velocidad por ronda (por defecto: 0.5)
speedIncreasePerRound: 0.5
```

---

**¡Que te diviertas cazando patos!** 🦆🔫
