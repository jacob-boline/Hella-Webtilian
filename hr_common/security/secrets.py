# hr_common/security/secrets.py

import os
from pathlib import Path


def read_secret(name: str) -> str | None:
    '''
    Read secret from either:
        - <NAME>_FILE (Docker secrets)
        - <NAME> (plain env var)
    '''
    file_path = os.getenv(f'{name}_FILE')
    if file_path:
        return Path(file_path).read_text().strip()
    return os.getenv(name)
