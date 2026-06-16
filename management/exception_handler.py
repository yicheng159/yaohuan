from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is None:
        return None
    
    # 如果有详细错误信息，返回详细信息，否则返回默认消息
    if 'detail' in response.data:
        message = response.data.get('detail', '请求失败')
    elif isinstance(response.data, dict) and any(isinstance(v, list) for v in response.data.values()):
        # 序列化器验证错误
        errors = []
        for field, messages in response.data.items():
            if isinstance(messages, list):
                errors.extend([f"{field}: {msg}" for msg in messages])
            else:
                errors.append(f"{field}: {messages}")
        message = "; ".join(errors)
    else:
        message = '请求失败'
    
    return Response({
        'code': response.status_code,
        'message': message
    }, status=response.status_code)