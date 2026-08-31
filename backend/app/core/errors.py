from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType
from typing import Mapping


class ErrorCode(IntEnum):
    """Stable business error codes grouped by domain and resource."""

    SUCCESS = 0
    SYSTEM_ERROR = 1000
    INVALID_REQUEST = 1010
    UNAUTHORIZED = 1020
    INVALID_ACCESS_TOKEN = 1030

    USER_NOT_FOUND = 2101
    USER_VALIDATION_FAILED = 2111
    USER_CONFLICT = 2121
    AUTHENTICATION_FAILED = 2201
    REFRESH_TOKEN_INVALID = 2211

    PET_NOT_FOUND = 3101
    PET_VALIDATION_FAILED = 3111
    PET_CONFLICT = 3121
    PET_FORBIDDEN = 3131
    CARE_RULE_NOT_FOUND = 3201
    CARE_RULE_VALIDATION_FAILED = 3211
    PET_STATE_NOT_FOUND = 3301
    PET_STATE_VALIDATION_FAILED = 3311
    SPECIES_NOT_FOUND = 3401
    SPECIES_VALIDATION_FAILED = 3411

    EVENT_NOT_FOUND = 4101
    EVENT_VALIDATION_FAILED = 4111
    EVENT_FORBIDDEN = 4131

    FILE_NOT_FOUND = 5101
    FILE_VALIDATION_FAILED = 5111
    FILE_FORBIDDEN = 5131


@dataclass(frozen=True)
class ErrorMetadata:
    """HTTP response metadata associated with one business error code."""

    http_status: int
    message: str


_ERROR_METADATA: Mapping[ErrorCode, ErrorMetadata] = MappingProxyType(
    {
        ErrorCode.SYSTEM_ERROR: ErrorMetadata(500, "服务器暂时无法处理请求"),
        ErrorCode.INVALID_REQUEST: ErrorMetadata(400, "请求参数无效"),
        ErrorCode.UNAUTHORIZED: ErrorMetadata(401, "请先登录"),
        ErrorCode.INVALID_ACCESS_TOKEN: ErrorMetadata(401, "登录状态已失效"),
        ErrorCode.USER_NOT_FOUND: ErrorMetadata(404, "用户不存在"),
        ErrorCode.USER_VALIDATION_FAILED: ErrorMetadata(400, "用户信息无效"),
        ErrorCode.USER_CONFLICT: ErrorMetadata(409, "用户信息已存在"),
        ErrorCode.AUTHENTICATION_FAILED: ErrorMetadata(401, "用户名或密码错误"),
        ErrorCode.REFRESH_TOKEN_INVALID: ErrorMetadata(401, "刷新令牌无效或已过期"),
        ErrorCode.PET_NOT_FOUND: ErrorMetadata(404, "宠物不存在"),
        ErrorCode.PET_VALIDATION_FAILED: ErrorMetadata(400, "宠物信息无效"),
        ErrorCode.PET_CONFLICT: ErrorMetadata(409, "宠物信息已存在"),
        ErrorCode.PET_FORBIDDEN: ErrorMetadata(403, "无权操作该宠物"),
        ErrorCode.CARE_RULE_NOT_FOUND: ErrorMetadata(404, "护理规则不存在"),
        ErrorCode.CARE_RULE_VALIDATION_FAILED: ErrorMetadata(400, "护理规则无效"),
        ErrorCode.PET_STATE_NOT_FOUND: ErrorMetadata(404, "宠物状态不存在"),
        ErrorCode.PET_STATE_VALIDATION_FAILED: ErrorMetadata(400, "宠物状态无效"),
        ErrorCode.SPECIES_NOT_FOUND: ErrorMetadata(404, "物种不存在"),
        ErrorCode.SPECIES_VALIDATION_FAILED: ErrorMetadata(400, "物种信息无效"),
        ErrorCode.EVENT_NOT_FOUND: ErrorMetadata(404, "事件不存在"),
        ErrorCode.EVENT_VALIDATION_FAILED: ErrorMetadata(400, "事件信息无效"),
        ErrorCode.EVENT_FORBIDDEN: ErrorMetadata(403, "无权操作该事件"),
        ErrorCode.FILE_NOT_FOUND: ErrorMetadata(404, "文件不存在"),
        ErrorCode.FILE_VALIDATION_FAILED: ErrorMetadata(400, "文件信息无效"),
        ErrorCode.FILE_FORBIDDEN: ErrorMetadata(403, "无权操作该文件"),
    }
)


class BusinessError(Exception):
    """Represent an expected domain failure without coupling business code to HTTP."""

    def __init__(self, error_code: ErrorCode, context: Mapping[str, object] | None = None) -> None:
        self.error_code = error_code
        self.context = context or {}
        super().__init__(error_code.name)


def get_error_metadata(error_code: ErrorCode) -> ErrorMetadata:
    """Return stable HTTP and natural-language metadata for an error code."""
    return _ERROR_METADATA.get(error_code, _ERROR_METADATA[ErrorCode.SYSTEM_ERROR])
