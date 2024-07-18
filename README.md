# Założenia projektu

Celem projektu jest stworzenie systemu rozpoznawania numerów rejestracyjnych pojazdów, który będzie w stanie:
1. Wykrywać obecność pojazdów za pomocą czujnika odległości.
2. Przechwytywać obraz pojazdu za pomocą kamery.
3. Wykrywać i rozpoznawać numery rejestracyjne pojazdów z przechwyconego obrazu.
4. Sprawdzać, czy rozpoznany numer rejestracyjny znajduje się w bazie danych dozwolonych numerów.
5. Sygnalizować stan (dozwolony/niedozwolony) za pomocą diod LED.
6. Wyświetlać informacje o numerze rejestracyjnym na wyświetlaczu LCD.
7. Zapisywać dane dotyczące rozpoznanych numerów rejestracyjnych w lokalnej i zdalnej bazie danych.
8. Synchronizować dane między bazami danych.

## Warstwa sprzętowa

Wykorzytsane komponenty:
- Raspberry Pi 3B
- Kamera internetowa na USB
- Wyświetlacz Nokia 5110 LCD
- Czujnik odległości HC-SR04
- Diody LED (czerwona i zielona)
- Przewody połączeniowe
- Rezystory - 3x330Ω i 220Ω
- Płytka prototypowa

Wiecej informacji w sprawozdanie.pdf
