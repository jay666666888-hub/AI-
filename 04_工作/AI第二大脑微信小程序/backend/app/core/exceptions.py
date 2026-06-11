from fastapi import HTTPException, status

class APIException(HTTPException):
    """统一API异常基类"""
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message}
        )

class NotFoundException(APIException):
    """资源不存在"""
    def __init__(self, resource: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource}不存在",
            status_code=status.HTTP_404_NOT_FOUND
        )

class UnauthorizedException(APIException):
    """未授权"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class ForbiddenException(APIException):
    """禁止访问"""
    def __init__(self, message: str = "无权限"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class ValidationException(APIException):
    """数据验证失败"""
    def __init__(self, message: str):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

class BusinessException(APIException):
    """业务逻辑异常"""
    def __init__(self, message: str):
        super().__init__(
            code="BUSINESS_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )