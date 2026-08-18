from itertools import chain
from typing import Any, Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic._internal import _model_construction

####################################################################################################
# LLM Models
####################################################################################################


def _json_schema_slim(schema: dict[str, Any]) -> None:
    schema.pop("required")
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)


class _BaseModelAliasMeta(_model_construction.ModelMetaclass):
    def __new__(
        cls, name: str, bases: tuple[type[Any], ...], dct: Dict[str, Any], alias: Optional[str] = None, **kwargs: Any
    ) -> type:
        if alias:
            dct["__qualname__"] = alias
            name = alias
        return super().__new__(cls, name, bases, dct, json_schema_extra=_json_schema_slim, **kwargs)


class BaseModelAlias:
    class Model(BaseModel, metaclass=_BaseModelAliasMeta):
        @staticmethod
        def to_dataclass(pydantic: Any) -> Any:
            raise NotImplementedError

    def to_str(self) -> str:
        raise NotImplementedError


####################################################################################################
# LLM Dumping to strings
####################################################################################################


def dump_to_csv(
    data: Iterable[object],
    fields: List[str],
    separator: str = "\t",
    with_header: bool = False,
    **values: Dict[str, List[Any]],
) -> List[str]:
    rows = list(
        chain(
            (separator.join(chain(fields, values.keys())),) if with_header else (),
            chain(
                separator.join(
                    chain(
                        (str(getattr(d, field)).replace("\n", "  ").replace("\t", " ") for field in fields),
                        (str(v).replace("\n", "  ").replace("\t", " ") for v in vs),
                    )
                )
                for d, *vs in zip(data, *values.values())
            ),
        )
    )
    return rows


def dump_to_reference_list(data: Iterable[object], separator: str = "\n=====\n\n"):
    return [f"[{i + 1}]  {d}{separator}" for i, d in enumerate(data)]


####################################################################################################
# Response Models
####################################################################################################


class TAnswer(BaseModel):
    answer: str


class THallazgoClave(BaseModel):
    titulo: str = Field(..., description="Título breve del hallazgo (máx. 8 palabras)")
    detalle: str = Field(..., description="Explicación del hallazgo basada en las fuentes")
    fuentes: List[int] = Field(
        default_factory=list,
        description="IDs numéricos de las fuentes que respaldan este hallazgo",
    )


class TViolacionPresunta(BaseModel):
    titulo: str = Field(
        ...,
        description=(
            "Nombre de la presunta violación de DD.HH., terminando en punto. "
            "Ej: 'Trata de personas y trabajo forzado.'"
        ),
    )
    analisis: str = Field(
        ...,
        description="Párrafo de análisis jurídico sistemático que explica por qué aplica al caso",
    )
    fuentes: List[int] = Field(
        default_factory=list,
        description="IDs de las fuentes que respaldan este análisis",
    )


class TTratadoAplicable(BaseModel):
    instrumento: str = Field(..., description="Nombre del tratado o instrumento internacional")
    articulos_clave: str = Field(
        ...,
        description="Artículos relevantes separados por comas. Ej: 'Arts. 2, 3, 6, 9, 11, 19, 32, 34'",
    )
    observaciones: Optional[str] = Field(
        None,
        description="Observaciones de organismos internacionales citadas en las fuentes, si aplica",
    )


class TObservacionResolucionInforme(BaseModel):
    tipo: str = Field(
        ...,
        description=(
            "Clase de fuente: Observación general, Resolución, Reporte o Informe. "
            "Usa exactamente una de esas etiquetas."
        ),
    )
    titulo: str = Field(
        ...,
        description="Nombre o cita de la observación general, resolución, reporte o informe",
    )
    organismo: Optional[str] = Field(
        None,
        description="Comité, relatoría, consejo u órgano que la emitió, si consta en las fuentes",
    )
    relevancia: str = Field(
        ...,
        description="Cómo aplica a la consulta, con referencias [n] al final si hay fuentes",
    )
    fuentes: List[int] = Field(
        default_factory=list,
        description="IDs de las fuentes que respaldan este ítem",
    )


class TStructuredQueryAnswer(BaseModel):
    """Respuesta jurídica estructurada al estilo análisis sistemático (Claude)."""

    razonamiento: str = Field(
        ...,
        description="Análisis interno paso a paso antes de redactar la respuesta final",
    )
    introduccion: str = Field(
        ...,
        description="Párrafo introductorio breve que contextualiza el caso y el enfoque del análisis",
    )
    violaciones: List[TViolacionPresunta] = Field(
        default_factory=list,
        description="Lista de presuntas violaciones de derechos humanos identificadas",
        max_length=8,
    )
    tratados: List[TTratadoAplicable] = Field(
        default_factory=list,
        description="Tratados e instrumentos internacionales aplicables con artículos clave",
        max_length=15,
    )
    observaciones_resoluciones: List[TObservacionResolucionInforme] = Field(
        default_factory=list,
        description=(
            "Observaciones generales, resoluciones, reportes e informes de órganos "
            "de tratados, relatorías y mecanismos aplicables a la consulta"
        ),
        max_length=12,
    )
    conclusion: Optional[str] = Field(
        None,
        description="Párrafo de cierre sobre convergencia de violaciones o vías de protección",
    )
    confianza: Literal["alta", "media", "baja"] = Field(
        ...,
        description="Nivel de confianza según la evidencia disponible en las fuentes",
    )
    limitaciones: Optional[str] = Field(
        None,
        description="Información no encontrada, ambigua o insuficiente en las fuentes",
    )


class TEditRelation(BaseModel):
    ids: List[int] = Field(..., description="Ids of the facts that you are combining into one")
    description: str = Field(
        ..., description="Summarized description of the combined facts, in detail and comprehensive"
    )


class TEditRelationList(BaseModel):
    groups: List[TEditRelation] = Field(
        ...,
        description="List of new fact groups; include only groups of more than one fact",
        alias="grouped_facts",
    )


class TEntityDescription(BaseModel):
    description: str


class TQueryEntities(BaseModel):
    named: List[str] = Field(
        ...,
        description=("List of named entities extracted from the query"),
    )
    generic: List[str] = Field(
        ...,
        description=("List of generic entities extracted from the query"),
    )

    @field_validator("named", mode="before")
    @classmethod
    def uppercase_named(cls, value: List[str]):
        return [e.upper() for e in value] if value else value

    # @field_validator("generic", mode="before")
    # @classmethod
    # def uppercase_generic(cls, value: List[str]):
    #     return [e.upper() for e in value] if value else value
