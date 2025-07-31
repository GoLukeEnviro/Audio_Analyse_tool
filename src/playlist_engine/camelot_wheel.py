"""Camelot Wheel - Tonart-Kompatibilität für DJ-Mixing"""

from typing import Dict, List, Optional, Tuple
import math


class CamelotWheel:
    """Implementierung des Camelot Wheel Systems für harmonische Mixing"""
    
    def __init__(self):
        # Camelot Wheel Mapping
        self.camelot_to_key = {
            # Major Keys (B = dur)
            '1B': 'C major', '2B': 'G major', '3B': 'D major', '4B': 'A major',
            '5B': 'E major', '6B': 'B major', '7B': 'F# major', '8B': 'Db major',
            '9B': 'Ab major', '10B': 'Eb major', '11B': 'Bb major', '12B': 'F major',
            
            # Minor Keys (A = moll)
            '1A': 'A minor', '2A': 'E minor', '3A': 'B minor', '4A': 'F# minor',
            '5A': 'C# minor', '6A': 'G# minor', '7A': 'D# minor', '8A': 'Bb minor',
            '9A': 'F minor', '10A': 'C minor', '11A': 'G minor', '12A': 'D minor'
        }
        
        # Reverse mapping
        self.key_to_camelot_map = {v: k for k, v in self.camelot_to_key.items()}
        
        # Alternative key notations
        self.key_aliases = {
            # Sharp/Flat equivalents
            'C# major': 'Db major', 'D# major': 'Eb major', 'F# major': 'Gb major',
            'G# major': 'Ab major', 'A# major': 'Bb major',
            'C# minor': 'Db minor', 'D# minor': 'Eb minor', 'F# minor': 'Gb minor',
            'G# minor': 'Ab minor', 'A# minor': 'Bb minor',
            
            # Different notation styles
            'C maj': 'C major', 'C min': 'C minor',
            'C': 'C major', 'Cm': 'C minor',
            'Am': 'A minor', 'Dm': 'D minor', 'Em': 'E minor',
            'Fm': 'F minor', 'Gm': 'G minor', 'Bm': 'B minor',
            
            # German notation
            'C dur': 'C major', 'C moll': 'C minor',
            'D dur': 'D major', 'D moll': 'D minor',
            'E dur': 'E major', 'E moll': 'E minor',
            'F dur': 'F major', 'F moll': 'F minor',
            'G dur': 'G major', 'G moll': 'G minor',
            'A dur': 'A major', 'A moll': 'A minor',
            'B dur': 'B major', 'B moll': 'B minor',
            'H dur': 'B major', 'H moll': 'B minor',
            
            # Flat/Sharp variations
            'Db dur': 'Db major', 'Eb dur': 'Eb major', 'Gb dur': 'F# major',
            'Ab dur': 'Ab major', 'Bb dur': 'Bb major',
            'Db moll': 'Bb minor', 'Eb moll': 'C minor', 'Gb moll': 'F# minor',
            'Ab moll': 'F minor', 'Bb moll': 'Bb minor'
        }
        
        # Kompatibilitäts-Regeln für Camelot Wheel
        self.compatibility_rules = {
            'perfect': 0,      # Gleiche Tonart
            'adjacent': 1,     # Benachbarte Positionen (+/-1)
            'relative': None,  # Relative Dur/Moll (A/B Wechsel)
            'dominant': 7,     # Dominante (+7 oder -5)
            'subdominant': 5   # Subdominante (+5 oder -7)
        }
    
    def normalize_key(self, key: str) -> str:
        """Normalisiert Tonart-Notation"""
        if not key:
            return ''
        
        key = key.strip()
        
        # Prüfe Aliases
        if key in self.key_aliases:
            return self.key_aliases[key]
        
        # Versuche case-insensitive matching
        for alias, normalized in self.key_aliases.items():
            if key.lower() == alias.lower():
                return normalized
        
        return key
    
    def key_to_camelot(self, key: str) -> Optional[str]:
        """Konvertiert Tonart zu Camelot-Notation"""
        normalized_key = self.normalize_key(key)
        return self.key_to_camelot_map.get(normalized_key)
    
    def camelot_to_key(self, camelot: str) -> Optional[str]:
        """Konvertiert Camelot-Notation zu Tonart"""
        return self.camelot_to_key.get(camelot)
    
    def parse_camelot(self, camelot: str) -> Tuple[int, str]:
        """Parst Camelot-Notation in Nummer und Typ (A/B)"""
        if not camelot or len(camelot) < 2:
            return 0, ''
        
        try:
            number = int(camelot[:-1])
            key_type = camelot[-1].upper()
            return number, key_type
        except (ValueError, IndexError):
            return 0, ''
    
    def build_camelot(self, number: int, key_type: str) -> str:
        """Erstellt Camelot-Notation aus Nummer und Typ"""
        if not (1 <= number <= 12) or key_type not in ['A', 'B']:
            return ''
        return f"{number}{key_type}"
    
    def get_adjacent_keys(self, camelot: str) -> List[str]:
        """Gibt benachbarte Tonarten zurück (+/-1 Position)"""
        number, key_type = self.parse_camelot(camelot)
        if not number or not key_type:
            return []
        
        adjacent = []
        
        # Vorherige Position (mit Wrap-around)
        prev_num = 12 if number == 1 else number - 1
        adjacent.append(self.build_camelot(prev_num, key_type))
        
        # Nächste Position (mit Wrap-around)
        next_num = 1 if number == 12 else number + 1
        adjacent.append(self.build_camelot(next_num, key_type))
        
        return adjacent
    
    def get_relative_key(self, camelot: str) -> Optional[str]:
        """Gibt die relative Dur/Moll-Tonart zurück"""
        number, key_type = self.parse_camelot(camelot)
        if not number or not key_type:
            return None
        
        # Wechsel zwischen A (moll) und B (dur)
        relative_type = 'B' if key_type == 'A' else 'A'
        return self.build_camelot(number, relative_type)
    
    def get_dominant_keys(self, camelot: str) -> List[str]:
        """Gibt Dominante-Tonarten zurück (+7/-5 Positionen)"""
        number, key_type = self.parse_camelot(camelot)
        if not number or not key_type:
            return []
        
        dominants = []
        
        # +7 Position (Dominante)
        dom_num = ((number + 7 - 1) % 12) + 1
        dominants.append(self.build_camelot(dom_num, key_type))
        
        # -5 Position (auch Dominante)
        sub_num = ((number - 5 - 1) % 12) + 1
        dominants.append(self.build_camelot(sub_num, key_type))
        
        return dominants
    
    def get_subdominant_keys(self, camelot: str) -> List[str]:
        """Gibt Subdominante-Tonarten zurück (+5/-7 Positionen)"""
        number, key_type = self.parse_camelot(camelot)
        if not number or not key_type:
            return []
        
        subdominants = []
        
        # +5 Position (Subdominante)
        sub_num = ((number + 5 - 1) % 12) + 1
        subdominants.append(self.build_camelot(sub_num, key_type))
        
        # -7 Position (auch Subdominante)
        dom_num = ((number - 7 - 1) % 12) + 1
        subdominants.append(self.build_camelot(dom_num, key_type))
        
        return subdominants
    
    def get_compatible_keys(self, camelot: str, compatibility_level: str = 'adjacent') -> List[str]:
        """Gibt kompatible Tonarten basierend auf Kompatibilitätslevel zurück"""
        if not camelot:
            return []
        
        compatible = [camelot]  # Immer mit sich selbst kompatibel
        
        if compatibility_level == 'perfect':
            return compatible
        
        elif compatibility_level == 'adjacent':
            compatible.extend(self.get_adjacent_keys(camelot))
            relative = self.get_relative_key(camelot)
            if relative:
                compatible.append(relative)
        
        elif compatibility_level == 'extended':
            compatible.extend(self.get_adjacent_keys(camelot))
            relative = self.get_relative_key(camelot)
            if relative:
                compatible.append(relative)
                # Auch benachbarte der relativen Tonart
                compatible.extend(self.get_adjacent_keys(relative))
        
        elif compatibility_level == 'harmonic':
            compatible.extend(self.get_adjacent_keys(camelot))
            relative = self.get_relative_key(camelot)
            if relative:
                compatible.append(relative)
            compatible.extend(self.get_dominant_keys(camelot))
            compatible.extend(self.get_subdominant_keys(camelot))
        
        elif compatibility_level == 'all':
            # Alle Tonarten des gleichen Typs (A oder B)
            number, key_type = self.parse_camelot(camelot)
            if key_type:
                for i in range(1, 13):
                    compatible.append(self.build_camelot(i, key_type))
        
        # Entferne Duplikate und leere Strings
        return list(set(filter(None, compatible)))
    
    def are_compatible(self, camelot1: str, camelot2: str, compatibility_level: str = 'adjacent') -> bool:
        """Prüft ob zwei Tonarten kompatibel sind"""
        if not camelot1 or not camelot2:
            return False
        
        compatible_keys = self.get_compatible_keys(camelot1, compatibility_level)
        return camelot2 in compatible_keys
    
    def calculate_distance(self, camelot1: str, camelot2: str) -> float:
        """Berechnet die harmonische Distanz zwischen zwei Tonarten"""
        if not camelot1 or not camelot2:
            return float('inf')
        
        if camelot1 == camelot2:
            return 0.0
        
        num1, type1 = self.parse_camelot(camelot1)
        num2, type2 = self.parse_camelot(camelot2)
        
        if not num1 or not num2:
            return float('inf')
        
        # Berechne Positions-Distanz (kürzester Weg um den Kreis)
        pos_diff = abs(num1 - num2)
        pos_distance = min(pos_diff, 12 - pos_diff)
        
        # Typ-Distanz (A vs B)
        type_distance = 0 if type1 == type2 else 0.5
        
        # Relative Tonart hat spezielle Behandlung
        if num1 == num2 and type1 != type2:
            return 0.1  # Sehr nah, da relative Tonart
        
        # Kombiniere Distanzen
        total_distance = pos_distance + type_distance
        
        return total_distance
    
    def get_transition_quality(self, from_camelot: str, to_camelot: str) -> str:
        """Bewertet die Qualität eines Übergangs zwischen zwei Tonarten"""
        distance = self.calculate_distance(from_camelot, to_camelot)
        
        if distance == 0:
            return 'Perfect'
        elif distance <= 0.1:
            return 'Excellent'  # Relative Tonart
        elif distance <= 1.0:
            return 'Good'       # Benachbarte Tonart
        elif distance <= 2.0:
            return 'Fair'       # 2 Positionen entfernt
        elif distance <= 3.0:
            return 'Poor'       # 3 Positionen entfernt
        else:
            return 'Bad'        # Weit entfernt
    
    def suggest_next_keys(self, current_camelot: str, energy_direction: str = 'maintain') -> List[Tuple[str, str, float]]:
        """Schlägt nächste Tonarten basierend auf aktueller Tonart und Energie-Richtung vor"""
        if not current_camelot:
            return []
        
        suggestions = []
        
        # Perfekte Matches (gleiche Tonart)
        suggestions.append((current_camelot, 'Perfect', 1.0))
        
        # Relative Tonart
        relative = self.get_relative_key(current_camelot)
        if relative:
            suggestions.append((relative, 'Relative', 0.95))
        
        # Benachbarte Tonarten
        for adjacent in self.get_adjacent_keys(current_camelot):
            suggestions.append((adjacent, 'Adjacent', 0.85))
        
        # Energie-basierte Vorschläge
        number, key_type = self.parse_camelot(current_camelot)
        
        if energy_direction == 'increase':
            # +1 Position für Energie-Anstieg
            next_num = 1 if number == 12 else number + 1
            energy_key = self.build_camelot(next_num, key_type)
            suggestions.append((energy_key, 'Energy Up', 0.8))
            
        elif energy_direction == 'decrease':
            # -1 Position für Energie-Abfall
            prev_num = 12 if number == 1 else number - 1
            energy_key = self.build_camelot(prev_num, key_type)
            suggestions.append((energy_key, 'Energy Down', 0.8))
        
        # Entferne Duplikate und sortiere nach Score
        unique_suggestions = {}
        for camelot, reason, score in suggestions:
            if camelot not in unique_suggestions or unique_suggestions[camelot][1] < score:
                unique_suggestions[camelot] = (reason, score)
        
        result = [(camelot, reason, score) for camelot, (reason, score) in unique_suggestions.items()]
        result.sort(key=lambda x: x[2], reverse=True)
        
        return result
    
    def get_all_keys(self) -> Dict[str, str]:
        """Gibt alle verfügbaren Tonarten zurück"""
        return self.camelot_to_key.copy()
    
    def get_wheel_position(self, camelot: str) -> Tuple[float, float]:
        """Gibt die Position auf dem Camelot Wheel zurück (x, y Koordinaten)"""
        number, key_type = self.parse_camelot(camelot)
        if not number:
            return 0.0, 0.0
        
        # Berechne Winkel (12 Uhr = 0°, im Uhrzeigersinn)
        angle = (number - 1) * 30  # 360° / 12 = 30° pro Position
        angle_rad = math.radians(angle - 90)  # -90° um bei 12 Uhr zu starten
        
        # Radius basierend auf Typ (A = innen, B = außen)
        radius = 0.7 if key_type == 'A' else 1.0
        
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        
        return x, y
    
    def find_key_center(self, keys: List[str]) -> Optional[str]:
        """Findet die zentrale Tonart einer Liste von Tonarten"""
        if not keys:
            return None
        
        camelot_keys = [self.key_to_camelot(key) for key in keys]
        camelot_keys = [ck for ck in camelot_keys if ck]  # Entferne None-Werte
        
        if not camelot_keys:
            return None
        
        if len(camelot_keys) == 1:
            return self.camelot_to_key(camelot_keys[0])
        
        # Berechne Zentrum basierend auf Positionen
        total_x, total_y = 0.0, 0.0
        
        for camelot in camelot_keys:
            x, y = self.get_wheel_position(camelot)
            total_x += x
            total_y += y
        
        center_x = total_x / len(camelot_keys)
        center_y = total_y / len(camelot_keys)
        
        # Finde nächste Tonart zum Zentrum
        min_distance = float('inf')
        closest_camelot = camelot_keys[0]
        
        for camelot in camelot_keys:
            x, y = self.get_wheel_position(camelot)
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_camelot = camelot
        
        return self.camelot_to_key(closest_camelot)