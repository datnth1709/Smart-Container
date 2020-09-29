#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from django.http import JsonResponse
from rest_framework.decorators import api_view


@api_view(['GET', 'POST', 'PUT'])
def rm_tmp(request):
    try:
        params = request.query_params
        file_name = params['file_name'].split(' ')[1]

        print(f'rm_tmp: file_name = {file_name}')

    except Exception as exc:
        print(exc)

    return JsonResponse({

    }, safe=False)
