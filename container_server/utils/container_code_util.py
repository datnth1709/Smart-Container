#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

from config.settings import log


class ContainerCodeUtil:
    @classmethod
    def extract_info(cls, container_str):
        container_code = ''
        length = '-'
        height = '-'

        try:
            # part1 = container_code[:10]
            # part2 = container_code[10]
            # part3 = container_code[11:15]
            #
            # container_owner_code = container_code[:3]
            # container_type_char = container_code[3]
            # container_type = CONTAINER_TYPES[container_type_char]
            container_code = container_str.replace(container_str[-5:-1], '')
            length = container_str[-5]
            length = length if length in ('2', '4', 'L', 'M') else '-'

            height = container_str[-4]
            height = height if height in ('0', '2', '5') else '-'

        except Exception as exc:
            log.error(f'Extract container info failed: {exc}')

        return container_code, length, height
