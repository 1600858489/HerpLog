from enum import StrEnum


class PetSex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class PetOriginType(StrEnum):
    SELF_BRED = "self_bred"
    BREEDER = "breeder"
    PURCHASED = "purchased"
    UNKNOWN = "unknown"


class PetParentRole(StrEnum):
    SIRE = "sire"
    DAM = "dam"
    UNSPECIFIED = "unspecified"


class ConfidenceLevel(StrEnum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    UNKNOWN = "unknown"


class InheritanceMode(StrEnum):
    DOMINANT = "dominant"
    RECESSIVE = "recessive"
    INCOMPLETE_DOMINANT = "incomplete_dominant"
    CODOMINANT = "codominant"
    UNKNOWN = "unknown"
