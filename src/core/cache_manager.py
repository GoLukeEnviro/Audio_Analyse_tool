import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheManager:
    """Erweiterte Cache-Verwaltung für Audio-Analysen mit Versionierung"""
    
    def __init__(self, cache_dir: str = None, cache_version: str = "2.0"):
        self.cache_version = cache_version
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".dj_tool_cache")
        self.cache_file = os.path.join(self.cache_dir, "analysis_cache.json")
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        
        # Cache-Einstellungen
        self.max_cache_size_mb = 100  # Maximum 100MB Cache
        self.max_cache_age_days = 30  # Cache-Einträge älter als 30 Tage löschen
        self.auto_cleanup = True
        
        self._ensure_cache_dir()
        self._load_cache()
        
        if self.auto_cleanup:
            self._cleanup_cache()
    
    def _ensure_cache_dir(self):
        """Stellt sicher, dass das Cache-Verzeichnis existiert"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_cache(self):
        """Lädt den Cache aus der Datei"""
        self.cache = {}
        self.metadata = {
            'version': self.cache_version,
            'created_at': datetime.now().isoformat(),
            'last_cleanup': datetime.now().isoformat(),
            'total_entries': 0,
            'cache_size_bytes': 0
        }
        
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                # Versionsprüfung
                if cache_data.get('version') == self.cache_version:
                    self.cache = cache_data.get('entries', {})
                else:
                    logger.info(f"Cache-Version {cache_data.get('version')} != {self.cache_version}, Cache wird geleert")
                    self._clear_cache()
            
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata.update(json.load(f))
                    
        except Exception as e:
            logger.error(f"Fehler beim Laden des Cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Speichert den Cache in die Datei"""
        try:
            cache_data = {
                'version': self.cache_version,
                'created_at': self.metadata.get('created_at'),
                'last_updated': datetime.now().isoformat(),
                'entries': self.cache
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # Metadaten aktualisieren
            self.metadata['total_entries'] = len(self.cache)
            self.metadata['cache_size_bytes'] = os.path.getsize(self.cache_file)
            self.metadata['last_updated'] = datetime.now().isoformat()
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Cache: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Berechnet einen Hash für die Datei basierend auf Pfad und Änderungszeit"""
        try:
            stat = os.stat(file_path)
            hash_input = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def get_cached_analysis(self, file_path: str) -> Optional[Dict]:
        """Ruft eine gecachte Analyse ab"""
        file_hash = self._get_file_hash(file_path)
        
        if file_hash in self.cache:
            cached_entry = self.cache[file_hash]
            
            # Prüfe Alter des Cache-Eintrags
            cached_time = datetime.fromisoformat(cached_entry.get('cached_at', datetime.now().isoformat()))
            if datetime.now() - cached_time > timedelta(days=self.max_cache_age_days):
                del self.cache[file_hash]
                self._save_cache()
                return None
            
            # Aktualisiere Zugriffszeitpunkt
            cached_entry['last_accessed'] = datetime.now().isoformat()
            cached_entry['access_count'] = cached_entry.get('access_count', 0) + 1
            
            logger.debug(f"Cache-Treffer für {file_path}")
            return cached_entry['analysis']
        
        return None
    
    def cache_analysis(self, file_path: str, analysis: Dict):
        """Speichert eine Analyse im Cache"""
        file_hash = self._get_file_hash(file_path)
        
        cache_entry = {
            'file_path': file_path,
            'analysis': analysis,
            'cached_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 1,
            'cache_version': self.cache_version
        }
        
        self.cache[file_hash] = cache_entry
        self._save_cache()
        
        logger.debug(f"Analyse für {file_path} gecacht")
    
    def remove_cached_analysis(self, file_path: str) -> bool:
        """Entfernt eine gecachte Analyse"""
        file_hash = self._get_file_hash(file_path)
        
        if file_hash in self.cache:
            del self.cache[file_hash]
            self._save_cache()
            logger.debug(f"Cache-Eintrag für {file_path} entfernt")
            return True
        
        return False
    
    def _cleanup_cache(self):
        """Bereinigt den Cache von alten und ungültigen Einträgen"""
        if not self.cache:
            return
        
        removed_count = 0
        current_time = datetime.now()
        
        # Entferne alte Einträge
        to_remove = []
        for file_hash, entry in self.cache.items():
            cached_time = datetime.fromisoformat(entry.get('cached_at', current_time.isoformat()))
            
            # Entferne wenn zu alt
            if current_time - cached_time > timedelta(days=self.max_cache_age_days):
                to_remove.append(file_hash)
                continue
            
            # Entferne wenn Datei nicht mehr existiert
            if not os.path.exists(entry.get('file_path', '')):
                to_remove.append(file_hash)
                continue
        
        for file_hash in to_remove:
            del self.cache[file_hash]
            removed_count += 1
        
        # Prüfe Cache-Größe
        if os.path.exists(self.cache_file):
            cache_size_mb = os.path.getsize(self.cache_file) / (1024 * 1024)
            
            if cache_size_mb > self.max_cache_size_mb:
                # Entferne die am wenigsten genutzten Einträge
                sorted_entries = sorted(
                    self.cache.items(),
                    key=lambda x: (x[1].get('access_count', 0), x[1].get('last_accessed', ''))
                )
                
                entries_to_remove = len(sorted_entries) // 4  # Entferne 25%
                for i in range(entries_to_remove):
                    file_hash = sorted_entries[i][0]
                    del self.cache[file_hash]
                    removed_count += 1
        
        if removed_count > 0:
            self._save_cache()
            self.metadata['last_cleanup'] = current_time.isoformat()
            logger.info(f"Cache bereinigt: {removed_count} Einträge entfernt")
    
    def _clear_cache(self):
        """Löscht den gesamten Cache"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        logger.info("Cache vollständig geleert")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück"""
        cache_size_bytes = 0
        if os.path.exists(self.cache_file):
            cache_size_bytes = os.path.getsize(self.cache_file)
        
        total_access_count = sum(entry.get('access_count', 0) for entry in self.cache.values())
        
        return {
            'version': self.cache_version,
            'total_entries': len(self.cache),
            'cache_size_bytes': cache_size_bytes,
            'cache_size_mb': cache_size_bytes / (1024 * 1024),
            'total_access_count': total_access_count,
            'cache_dir': self.cache_dir,
            'last_cleanup': self.metadata.get('last_cleanup'),
            'created_at': self.metadata.get('created_at')
        }
    
    def export_cache(self, export_path: str) -> bool:
        """Exportiert den Cache in eine Datei"""
        try:
            export_data = {
                'version': self.cache_version,
                'exported_at': datetime.now().isoformat(),
                'metadata': self.metadata,
                'cache': self.cache
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cache nach {export_path} exportiert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Cache-Export: {e}")
            return False
    
    def import_cache(self, import_path: str) -> bool:
        """Importiert einen Cache aus einer Datei"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Versionsprüfung
            if import_data.get('version') != self.cache_version:
                logger.warning(f"Import-Version {import_data.get('version')} != {self.cache_version}")
                return False
            
            # Merge mit existierendem Cache
            imported_cache = import_data.get('cache', {})
            self.cache.update(imported_cache)
            
            self._save_cache()
            logger.info(f"Cache aus {import_path} importiert: {len(imported_cache)} Einträge")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Cache-Import: {e}")
            return False