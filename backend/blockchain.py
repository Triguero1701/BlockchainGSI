import hashlib
import json
from time import time

class Bloque:
    def __init__(self, index, previous_hash, payload, timestamp=None):
        self.index = index
        self.timestamp = timestamp or time()
        self.payload = payload  # Payload contains db_id, id_lote, lat, lon, temperatura
        self.previous_hash = previous_hash
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        # We ensure consistent ordering with sort_keys=True
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode('utf-8')
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.cadena = []
        self.crear_bloque_genesis()

    def crear_bloque_genesis(self):
        genesis = Bloque(0, "0" * 64, {"mensaje": "Bloque Genesis"}, timestamp=0)
        self.cadena.append(genesis)

    def get_ultimo_bloque(self):
        return self.cadena[-1]

    def agregar_bloque(self, payload):
        ultimo_bloque = self.get_ultimo_bloque()
        nuevo_bloque = Bloque(index=len(self.cadena), previous_hash=ultimo_bloque.hash, payload=payload)
        self.cadena.append(nuevo_bloque)
        return nuevo_bloque

    def validar_cadena(self):
        """
        Valida que todos los hashes coincidan (integridad temporal).
        Retorna (True, -1) si es correcta, o (False, index) indicando el bloque roto.
        """
        for i in range(1, len(self.cadena)):
            actual = self.cadena[i]
            anterior = self.cadena[i-1]

            # 1. Comprobar que el hash del bloque es correcto según sus datos actuales
            if actual.hash != actual.calcular_hash():
                return False, i

            # 2. Comprobar que el previous_hash del actual apunta al anterior (cadena intacta)
            if actual.previous_hash != anterior.hash:
                return False, i

        return True, -1
