"""统一错误处理装饰器 + 全局异常处理"""
import logging
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def safe_api(func: Callable) -> Callable:
    """API 端点统一错误处理装饰器"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except IntegrityError as e:
            logger.warning(f"数据完整性错误: {e}")
            raise HTTPException(status_code=400, detail="数据冲突，请检查后重试")
        except SQLAlchemyError as e:
            logger.error(f"数据库错误: {e}")
            raise HTTPException(status_code=500, detail="数据库操作失败")
        except Exception as e:
            logger.error(f"未捕获异常 in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)[:200]}")

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except IntegrityError as e:
            logger.warning(f"数据完整性错误: {e}")
            raise HTTPException(status_code=400, detail="数据冲突，请检查后重试")
        except SQLAlchemyError as e:
            logger.error(f"数据库错误: {e}")
            raise HTTPException(status_code=500, detail="数据库操作失败")
        except Exception as e:
            logger.error(f"未捕获异常 in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)[:200]}")

    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def register_exception_handlers(app):
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误",
                "path": str(request.url),
            },
        )
