import json
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import Response

from errors import error_handler, ServiceError

from app.core.logger import get_logger
from app.repository.tgbot import Alert

logger = get_logger()


async def catch_exceptions_middleware(request: Request, call_next) -> Response:
    start_time = datetime.now()
    try:
        response = await call_next(request)
        if response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_422_UNPROCESSABLE_ENTITY):
            binary = b''
            async for data in response.body_iterator:
                binary += data
            body = binary.decode()
            raise ServiceError(9999, f'Framework error occurred: {json.loads(body).get("detail")}')
    except Exception as ex:
        Alert.critical(f'`❌ Ошибка во время обработки запроса:\n\n{ex}`')
        response_schema = error_handler(ex)
        response = JSONResponse(jsonable_encoder(response_schema))
    end_time = datetime.now()
    response_body = (
        response.body
        if hasattr(response, 'body') else
        {'status_code': response.status_code}
    )
    logger.warning(
        {
            'type': 'mw-request',
            'req': {'method': request.method,
                    'url': str(request.url)},
            'res': {'response': response_body},
            'time': str(end_time - start_time),
        },
    )
    return response
