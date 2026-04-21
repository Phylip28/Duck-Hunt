#!/usr/bin/env python3
"""
Duck Hunt - PRNG LCG Analysis (Notebook-style Execution)
Ejecución educativa del análisis de Números Aleatorios
"""

import sys
sys.path.insert(0, './src')

from duck_hunt.prng_lcg import LCG
import time

def main():
    # ========================================================================
    # SECCIÓN 1: Parámetros del LCG 32-bits
    # ========================================================================
    print("=" * 75)
    print("GENERADOR DE CONGRUENCIAS LINEALES - PARÁMETROS (32-BITS)")
    print("=" * 75)
    
    a = 1103515245
    c = 12345
    m = 2**32
    Xo = 12345
    
    print(f"a (Multiplicador):  {a:>15,}")
    print(f"c (Incremento):     {c:>15,}")
    print(f"m (Módulo):         {m:>15,}")
    print(f"Xo (Semilla):       {Xo:>15,}")
    print("=" * 75)
    
    # ========================================================================
    # SECCIÓN 2: Generación de números decimales
    # ========================================================================
    print("\n\nSECCIÓN 2: Números Decimales [0.0, 1.0)")
    print("-" * 75)
    
    prng = LCG(Xo)
    print("\nGenerando 10 números decimales:")
    print("-" * 75)
    
    for i in range(10):
        numero = prng.next_float()
        print(f"X_{i+1:2d} = {numero:.10f}")
    
    # ========================================================================
    # SECCIÓN 3: Simulación de dados (mapas)
    # ========================================================================
    print("\n\nSECCIÓN 3: Aplicación - Simulación de Dado (1-6) para Duck Hunt")
    print("=" * 75)
    
    prng.set_seed(Xo)
    
    Lim_1 = 1
    Lim_2 = 6
    
    Pendiente = (Lim_2 + 1 - Lim_1) / (1 - 0)
    Intercepto = Lim_1
    
    print(f"\nParámetros de mapeo:")
    print(f"  Límite inferior: {Lim_1}")
    print(f"  Límite superior: {Lim_2}")
    print(f"  Pendiente:       {Pendiente}")
    print(f"  Intercepto:      {Intercepto}")
    print("-" * 75)
    
    Num_samples = 20
    Lista_mapas = []
    
    print(f"\nSimulando {Num_samples} selecciones de mapa:")
    print("-" * 75)
    
    for i in range(Num_samples):
        numero_rango = prng.randint(Lim_1, Lim_2)
        Lista_mapas.append(numero_rango)
        if i < 10:
            print(f"Selección {i+1:2d}: Mapa {numero_rango}")
    
    print(f"... (mostrando solo las primeras 10)")
    print(f"\nSecuencia completa: {Lista_mapas}")
    
    # ========================================================================
    # SECCIÓN 4: Mapeos a mapas reales
    # ========================================================================
    print("\n\nSECCIÓN 4: Mapeo a Mapas Reales del Juego")
    print("=" * 75)
    
    mapas_disponibles = [
        "Bosque Oscuro",
        "Montaña Nevada",
        "Pantano Misterioso",
        "Playa Tropical",
        "Castillo Antiguo",
        "Cueva Subterránea"
    ]
    
    print("\nMapeos de selecciones a mapas reales:")
    print("-" * 75)
    
    for i in range(10):
        num_mapa = Lista_mapas[i]
        indice = (num_mapa - 1) % len(mapas_disponibles)
        mapa_seleccionado = mapas_disponibles[indice]
        print(f"Ronda {i+1:2d}: Selección={num_mapa} → Mapa: {mapa_seleccionado}")
    
    print(f"\n... (continuando con las rondas restantes)")
    
    # ========================================================================
    # SECCIÓN 5: Reproducibilidad
    # ========================================================================
    print("\n\nSECCIÓN 5: Verificación de Reproducibilidad")
    print("=" * 75)
    
    print("\nVERIFICACIÓN DE REPRODUCIBILIDAD")
    print("-" * 75)
    
    prng1 = LCG(99999)
    secuencia1 = [prng1.next_float() for _ in range(5)]
    
    prng2 = LCG(99999)
    secuencia2 = [prng2.next_float() for _ in range(5)]
    
    print("\nSecuencia 1 (Semilla=99999):")
    for i, val in enumerate(secuencia1, 1):
        print(f"  X_{i} = {val:.10f}")
    
    print("\nSecuencia 2 (Semilla=99999):")
    for i, val in enumerate(secuencia2, 1):
        print(f"  X_{i} = {val:.10f}")
    
    if secuencia1 == secuencia2:
        print("\n✓ REPRODUCIBILIDAD VERIFICADA")
        print("  Las secuencias son idénticas.")
        print("  Esto permite depurar y validar el juego.")
    else:
        print("\n✗ ERROR: Las secuencias no coinciden")
    
    # ========================================================================
    # SECCIÓN 6: Comparación 16-bits vs 32-bits
    # ========================================================================
    print("\n\nSECCIÓN 6: Comparación - LCG de 16-bits vs 32-bits")
    print("=" * 75)
    
    a_16 = 1103515245
    c_16 = 12345
    m_16 = 2**15
    
    a_32 = 1103515245
    c_32 = 12345
    m_32 = 2**32
    
    print("\n" + "-" * 75)
    print("\nCOMPARACIÓN: LCG de 16-bits vs 32-bits")
    print("-" * 75)
    print(f"{'Parámetro':<25} | {'LCG 16-bits':<20} | {'LCG 32-bits':<20}")
    print("-" * 75)
    print(f"{'Multiplicador (a)':<25} | {f'{a_16:,}':<20} | {f'{a_32:,}':<20}")
    print(f"{'Incremento (c)':<25} | {f'{c_16:,}':<20} | {f'{c_32:,}':<20}")
    print(f"{'Módulo (m)':<25} | {f'{m_16:,}':<20} | {f'{m_32:,}':<20}")
    print(f"{'Período máximo':<25} | {'2^15 = 32,768':<20} | {'2^32 = 4,294,967,296':<20}")
    print(f"{'Rango de valores':<25} | {'0 a 32,767':<20} | {'0 a 4,294,967,295':<20}")
    
    print("\n" + "-" * 75)
    print("\nVENTAJAS DEL LCG 32-BITS:")
    print("  1. Mayor período: 2^32 vs 2^15 = 131,072x más largo")
    print("  2. Mejor distribución: menos patrones predecibles")
    print("  3. Menos ciclos cortos: ideal para videojuegos largos")
    print("  4. Estándar moderno: usado en glibc/POSIX")
    print("  5. Más seguridad: en debug/testing")
    
    # ========================================================================
    # SECCIÓN 7: Simulación del juego
    # ========================================================================
    print("\n\nSECCIÓN 7: Ejecución del Juego Duck Hunt")
    print("=" * 75)
    
    print("\nSimulando una partida completa...")
    print("-" * 75)
    
    prng_game = LCG(42)
    
    print("\nRonda 1: Iniciando partida...")
    print("-" * 75)
    
    num_mapa = prng_game.randint(1, 6)
    mapas = ["Bosque", "Montaña", "Pantano", "Playa", "Castillo", "Cueva"]
    mapa_seleccionado = mapas[num_mapa - 1]
    
    print(f"Mapa seleccionado: {mapa_seleccionado}")
    
    num_enemigos = prng_game.randint(5, 10)
    print(f"Cantidad de enemigos: {num_enemigos}")
    
    aciertos = 0
    disparos = 0
    
    print("\nSimulando tiradas...")
    for i in range(num_enemigos):
        if prng_game.next_float() < 0.6:
            aciertos += 1
            resultado = "¡ACERTASTE! 💥"
        else:
            resultado = "Fallaste..."
        disparos += 1
        print(f"  Disparo {disparos}: {resultado}")
    
    puntuacion = aciertos * 100
    
    print("\n" + "-" * 75)
    print(f"\nResultados finales:")
    print(f"  Aciertos: {aciertos}/{disparos}")
    print(f"  Precisión: {(aciertos/disparos)*100:.1f}%")
    print(f"  Puntuación: {puntuacion} puntos")
    print("\n✓ Partida completada con PRNG LCG 32-bits")
    
    print("\n\nSECCIÓN 8: Integración en el Sistema del Juego")
    print("=" * 75)
    
    print("\n" + "=" * 100)
    print("\nINTEGRACIÓN EN EL SISTEMA DEL JUEGO")
    print("=" * 100)
    print(f"{'Componente':<25} | {'Usa PRNG':<30} | {'Archivo':<20}")
    print("-" * 100)
    print(f"{'Selector de mapas':<25} | {'✓ Sí (sin semilla)':<30} | {'ui_tk.py':<20}")
    print(f"{'Generador de enemigos':<25} | {'✓ Sí (con semilla)':<30} | {'game_state.py':<20}")
    print(f"{'Sistema de audio':<25} | {'✓ Reproducción aleatoria':<30} | {'audio.py':<20}")
    print(f"{'Efectos visuales':<25} | {'✓ Sangre y partículas':<30} | {'ui_tk.py':<20}")
    print(f"{'Sistema de ranking':<25} | {'✓ Probabilidades':<30} | {'storage.py':<20}")
    print(f"{'Lógica de juego':<25} | {'✓ Todo el juego':<30} | {'runtime.py':<20}")
    
    print("\n" + "=" * 75)
    print("\nPara ejecutar el juego completo, usa:")
    print("  $ uv run python -m duck_hunt")
    print("\n" + "=" * 75)
    
    # ========================================================================
    # CONCLUSIONES
    # ========================================================================
    print("\n\nCONCLUSIONES")
    print("=" * 75)
    
    print("\n✅ LCG es ideal para videojuegos")
    print("   - Rápido (O(1))")
    print("   - Determinista (reproducible)")
    print("   - Parámetros bien estudiados")
    
    print("\n✅ 32-bits vs 16-bits")
    print("   - Período 131,072x más largo")
    print("   - Mejor distribución estadística")
    print("   - Estándar moderno")
    
    print("\n✅ Implementación en Duck Hunt")
    print("   - Sin dependencias externas")
    print("   - Integrado en todo el sistema")
    print("   - Compatible con testing")
    
    print("\n✅ Educativo")
    print("   - Código bien documentado")
    print("   - Fácil de entender y modificar")
    print("   - Aplicable a otros proyectos")
    
    print("\n" + "=" * 75)
    print("\nEJECUCIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 75)


if __name__ == "__main__":
    main()
