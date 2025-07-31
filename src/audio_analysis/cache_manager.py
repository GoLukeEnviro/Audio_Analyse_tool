"""Cache Manager - Verwaltung von Analyse-Cache-Dateien"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from pathlib import Path


class CacheManager:
    """Verwaltet Cache-Dateien für Audio-Analyse-Ergebnisse"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache-Metadaten
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self.load_metadata()
        
    def load_metadata(self) -> Dict[str, Any]:
        """Lädt Cache-Metadaten"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache metadata: {e}")
        
        return {
            'created': time.time(),
            'last_cleanup': time.time(),
            'total_files': 0,
            'total_size_bytes': 0,
            'files': {}
        }
    
    def save_metadata(self):
        """Speichert Cache-Metadaten"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache metadata: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Berechnet MD5-Hash einer Datei"""
        try:
            hash_md5 = hashlib.md5()
            
            # Datei-Informationen für Hash
            stat = os.stat(file_path)
            file_info = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
            hash_md5.update(file_info.encode('utf-8'))
            
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return hashlib.md5(file_path.encode('utf-8')).hexdigest()
    
    def get_cache_path(self, file_path: str) -> Path:
        """Gibt den Cache-Pfad für eine Datei zurück"""
        file_hash = self.get_file_hash(file_path)
        return self.cache_dir / f"{file_hash}.json"
    
    def is_cached(self, file_path: str) -> bool:
        """Prüft ob eine Datei im Cache existiert"""
        cache_path = self.get_cache_path(file_path)
        
        if not cache_path.exists():
            return False
        
        # Prüfe ob die Original-Datei noch existiert und unverändert ist
        if not os.path.exists(file_path):
            return False
        
        try:
            # Prüfe Metadaten
            file_hash = self.get_file_hash(file_path)
            if file_hash in self.metadata['files']:
                cached_info = self.metadata['files'][file_hash]
                
                # Prüfe ob die Datei seit dem Caching verändert wurde
                current_mtime = os.path.getmtime(file_path)
                if abs(current_mtime - cached_info.get('original_mtime', 0)) > 1:
                    return False
                
                return True
        except Exception as e:
            print(f"Error checking cache for {file_path}: {e}")
        
        return False
    
    def load_from_cache(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Lädt Analyse-Ergebnisse aus dem Cache"""
        if not self.is_cached(file_path):
            return None
        
        cache_path = self.get_cache_path(file_path)
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update last accessed time
            file_hash = self.get_file_hash(file_path)
            if file_hash in self.metadata['files']:
                self.metadata['files'][file_hash]['last_accessed'] = time.time()
                self.save_metadata()
            
            return data
            
        except Exception as e:
            print(f"Error loading from cache {cache_path}: {e}")
            return None
    
    def save_to_cache(self, file_path: str, analysis_data: Dict[str, Any]) -> bool:
        """Speichert Analyse-Ergebnisse im Cache"""
        try:
            cache_path = self.get_cache_path(file_path)
            
            # Füge Cache-Metadaten hinzu
            cache_data = {
                'file_path': file_path,
                'cached_at': time.time(),
                'analysis_data': analysis_data
            }
            
            # Speichere Cache-Datei
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # Update Metadaten
            file_hash = self.get_file_hash(file_path)
            file_size = cache_path.stat().st_size
            
            self.metadata['files'][file_hash] = {
                'file_path': file_path,
                'cache_path': str(cache_path),
                'cached_at': time.time(),
                'last_accessed': time.time(),
                'original_mtime': os.path.getmtime(file_path),
                'cache_size_bytes': file_size
            }
            
            self.metadata['total_files'] = len(self.metadata['files'])
            self.metadata['total_size_bytes'] = sum(
                info.get('cache_size_bytes', 0) for info in self.metadata['files'].values()
            )
            
            self.save_metadata()
            return True
            
        except Exception as e:
            print(f"Error saving to cache {file_path}: {e}")
            return False
    
    def remove_from_cache(self, file_path: str) -> bool:
        """Entfernt eine Datei aus dem Cache"""
        try:
            cache_path = self.get_cache_path(file_path)
            file_hash = self.get_file_hash(file_path)
            
            # Lösche Cache-Datei
            if cache_path.exists():
                cache_path.unlink()
            
            # Update Metadaten
            if file_hash in self.metadata['files']:
                del self.metadata['files'][file_hash]
                
                self.metadata['total_files'] = len(self.metadata['files'])
                self.metadata['total_size_bytes'] = sum(
                    info.get('cache_size_bytes', 0) for info in self.metadata['files'].values()
                )
                
                self.save_metadata()
            
            return True
            
        except Exception as e:
            print(f"Error removing from cache {file_path}: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """Löscht den gesamten Cache"""
        try:
            # Lösche alle Cache-Dateien
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.name != "cache_metadata.json":
                    cache_file.unlink()
            
            # Reset Metadaten
            self.metadata = {
                'created': time.time(),
                'last_cleanup': time.time(),
                'total_files': 0,
                'total_size_bytes': 0,
                'files': {}
            }
            
            self.save_metadata()
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def cleanup_cache(self, max_age_days: int = 30, max_size_mb: int = 1000) -> Dict[str, int]:
        """Bereinigt den Cache basierend auf Alter und Größe"""
        removed_files = 0
        freed_bytes = 0
        
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            max_size_bytes = max_size_mb * 1024 * 1024
            
            files_to_remove = []
            
            # Sammle Dateien zum Entfernen (zu alt)
            for file_hash, info in self.metadata['files'].items():
                last_accessed = info.get('last_accessed', info.get('cached_at', 0))
                age = current_time - last_accessed
                
                if age > max_age_seconds:
                    files_to_remove.append(file_hash)
            
            # Entferne alte Dateien
            for file_hash in files_to_remove:
                info = self.metadata['files'][file_hash]
                cache_path = Path(info['cache_path'])
                
                if cache_path.exists():
                    cache_path.unlink()
                    freed_bytes += info.get('cache_size_bytes', 0)
                    removed_files += 1
                
                del self.metadata['files'][file_hash]
            
            # Prüfe Größenlimit
            if self.metadata['total_size_bytes'] > max_size_bytes:
                # Sortiere nach letztem Zugriff (älteste zuerst)
                sorted_files = sorted(
                    self.metadata['files'].items(),
                    key=lambda x: x[1].get('last_accessed', x[1].get('cached_at', 0))
                )
                
                current_size = self.metadata['total_size_bytes']
                
                for file_hash, info in sorted_files:
                    if current_size <= max_size_bytes:
                        break
                    
                    cache_path = Path(info['cache_path'])
                    
                    if cache_path.exists():
                        cache_path.unlink()
                        file_size = info.get('cache_size_bytes', 0)
                        freed_bytes += file_size
                        current_size -= file_size
                        removed_files += 1
                    
                    del self.metadata['files'][file_hash]
            
            # Update Metadaten
            self.metadata['total_files'] = len(self.metadata['files'])
            self.metadata['total_size_bytes'] = sum(
                info.get('cache_size_bytes', 0) for info in self.metadata['files'].values()
            )
            self.metadata['last_cleanup'] = current_time
            
            self.save_metadata()
            
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
        
        return {
            'removed_files': removed_files,
            'freed_bytes': freed_bytes,
            'freed_mb': freed_bytes / (1024 * 1024)
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück"""
        try:
            # Aktualisiere Größen-Informationen
            total_size = 0
            valid_files = 0
            
            for file_hash, info in list(self.metadata['files'].items()):
                cache_path = Path(info['cache_path'])
                
                if cache_path.exists():
                    size = cache_path.stat().st_size
                    total_size += size
                    valid_files += 1
                    
                    # Update size in metadata
                    self.metadata['files'][file_hash]['cache_size_bytes'] = size
                else:
                    # Entferne ungültige Einträge
                    del self.metadata['files'][file_hash]
            
            self.metadata['total_files'] = valid_files
            self.metadata['total_size_bytes'] = total_size
            
            return {
                'total_files': valid_files,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'cache_directory': str(self.cache_dir),
                'created': self.metadata.get('created', 0),
                'last_cleanup': self.metadata.get('last_cleanup', 0),
                'oldest_file': min(
                    (info.get('cached_at', 0) for info in self.metadata['files'].values()),
                    default=0
                ),
                'newest_file': max(
                    (info.get('cached_at', 0) for info in self.metadata['files'].values()),
                    default=0
                )
            }
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'cache_directory': str(self.cache_dir),
                'created': 0,
                'last_cleanup': 0,
                'oldest_file': 0,
                'newest_file': 0
            }
    
    def get_cached_files(self) -> List[Dict[str, Any]]:
        """Gibt eine Liste aller gecachten Dateien zurück"""
        cached_files = []
        
        for file_hash, info in self.metadata['files'].items():
            cache_path = Path(info['cache_path'])
            
            if cache_path.exists():
                cached_files.append({
                    'file_path': info['file_path'],
                    'cached_at': info.get('cached_at', 0),
                    'last_accessed': info.get('last_accessed', 0),
                    'cache_size_bytes': info.get('cache_size_bytes', 0),
                    'file_hash': file_hash
                })
        
        return sorted(cached_files, key=lambda x: x['last_accessed'], reverse=True)
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimiert den Cache durch Entfernung ungültiger Einträge"""
        removed_entries = 0
        freed_bytes = 0
        
        try:
            # Prüfe alle Cache-Einträge
            for file_hash, info in list(self.metadata['files'].items()):
                cache_path = Path(info['cache_path'])
                original_path = info['file_path']
                
                # Entferne Einträge für nicht existierende Original-Dateien
                if not os.path.exists(original_path):
                    if cache_path.exists():
                        freed_bytes += cache_path.stat().st_size
                        cache_path.unlink()
                    
                    del self.metadata['files'][file_hash]
                    removed_entries += 1
                    continue
                
                # Entferne Einträge für nicht existierende Cache-Dateien
                if not cache_path.exists():
                    del self.metadata['files'][file_hash]
                    removed_entries += 1
                    continue
                
                # Prüfe ob die Original-Datei verändert wurde
                try:
                    current_mtime = os.path.getmtime(original_path)
                    cached_mtime = info.get('original_mtime', 0)
                    
                    if abs(current_mtime - cached_mtime) > 1:
                        freed_bytes += cache_path.stat().st_size
                        cache_path.unlink()
                        del self.metadata['files'][file_hash]
                        removed_entries += 1
                except Exception:
                    # Bei Fehlern den Eintrag entfernen
                    if cache_path.exists():
                        freed_bytes += cache_path.stat().st_size
                        cache_path.unlink()
                    
                    del self.metadata['files'][file_hash]
                    removed_entries += 1
            
            # Update Metadaten
            self.metadata['total_files'] = len(self.metadata['files'])
            self.metadata['total_size_bytes'] = sum(
                info.get('cache_size_bytes', 0) for info in self.metadata['files'].values()
            )
            
            self.save_metadata()
            
        except Exception as e:
            print(f"Error during cache optimization: {e}")
        
        return {
            'removed_entries': removed_entries,
            'freed_bytes': freed_bytes,
            'freed_mb': freed_bytes / (1024 * 1024)
        }