"""수동 데이터 수집 스크립트.

프로젝트 루트에서 실행:
    python -m scripts.collect
"""

import logging

from app.collector import collect

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    summary = collect()
    print("수집 결과:", summary)
