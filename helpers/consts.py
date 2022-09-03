from django.conf import settings
from django.core.files.storage import FileSystemStorage

S3_REVIEW_IMAGE_BUCKET_STORAGE = FileSystemStorage(
    location="", base_url=settings.REVIEW_IMAGE_HOST
)

HOME_CATEGORY_UI_GUIDE_TEXT = {
    settings.OWN_DELIVERY_HOME_CATEGORY_CODE: "빠르게 먹고 싶을 땐, \n익스프레스!",  # 익스프레스
    settings.MART_HOME_CATEGORY_CODE: "빠르게 장보고 \n싶을 땐, 요마트!",  # 요마트
    settings.TAKEOUT_HOME_CATEGORY_CODE: "내 근처 가게, \n가볍게 \n받아오세요!",  # 포장
    settings.GIFT_HOME_CATEGORY_CODE: "든든한 한끼로 \n마음을 전하세요!",  # 선물하기
    settings.CONVENIENCE_STORE_HOME_CATEGORY_CODE: "간식도, 생활용품도 \n다 있어요!",  # 편의점/마트
}

DETAIL_IMAGE_S3_UPLOAD_DIR = "restaurants/detail_image"

VMS_FILE_PREFIX = "VMS:"
