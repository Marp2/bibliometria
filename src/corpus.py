"""Carga del corpus y calculo (una sola vez) de todo lo que reutilizan los requerimientos 1, 2 y 3."""
import json

from src.paths import find_data_file
from src.preprocesamiento import preprocesar
from src.similitud_clasica import calcular_idf, construir_vocabulario, vector_tfidf
from src.similitud_embeddings import cargar_modelos


class ErrorCorpus(Exception):
    """Error controlado (archivo faltante, articulo inexistente, etc.)."""


class Corpus:
    def __init__(self, ruta_corpus=None):
        ruta = ruta_corpus or find_data_file("corpus.json")
        if ruta is None:
            raise ErrorCorpus("No se encontro data/processed/corpus.json. Ejecute: python scripts/extraer_corpus.py")
        with open(str(ruta), encoding="utf-8") as f:
            self.documentos = json.load(f)
        if len(self.documentos) == 0:
            raise ErrorCorpus("El corpus esta vacio.")
        self._por_id = {}
        for d in self.documentos:
            d["pre"] = preprocesar(d["abstract"], usar_stemming=True)
            self._por_id[d["id"]] = d
        self.vocab = construir_vocabulario([d["pre"]["tokens_finales"] for d in self.documentos])
        self.idf = calcular_idf(self.vocab)
        for d in self.documentos:
            d["tfidf"] = vector_tfidf(d["pre"]["tokens_finales"], self.vocab, self.idf)
        self.modelos = cargar_modelos()

    def ids(self):
        return [d["id"] for d in self.documentos]

    def obtener(self, id_doc):
        try:
            clave = int(id_doc)
        except (TypeError, ValueError):
            raise ErrorCorpus("Identificador de articulo invalido: %r" % (id_doc,))
        if clave not in self._por_id:
            raise ErrorCorpus("El articulo %d no existe en el corpus (ids validos: %d a %d)." % (
                clave, min(self._por_id), max(self._por_id)))
        return self._por_id[clave]

    def resumen(self):
        """Lista liviana (sin vectores) para la interfaz."""
        return [{"id": d["id"], "titulo": d["titulo"], "autores": d["autores"],
                 "palabras": len(d["pre"]["tokens"]), "caracteres": len(d["abstract"])}
                for d in self.documentos]


_INSTANCIA = None


def obtener_corpus(recargar=False):
    global _INSTANCIA
    if _INSTANCIA is None or recargar:
        _INSTANCIA = Corpus()
    return _INSTANCIA
