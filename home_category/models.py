from datetime import datetime
from operator import attrgetter

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models, transaction

from helpers.consts import (DETAIL_IMAGE_S3_UPLOAD_DIR,
                            HOME_CATEGORY_UI_GUIDE_TEXT,
                            S3_REVIEW_IMAGE_BUCKET_STORAGE)
from helpers.enums import StrCodeEnum, StrLabelPairEnum
from helpers.s3 import get_s3_review_image_bucket_url


class HomeCategoryType(StrLabelPairEnum):
    DEFAULT = ("default", "음식")
    KEYWORD = ("keyword", "키워드")
    FUNCTION = ("function", "기능")


class HomeCategoryFetchType(StrLabelPairEnum):
    CLASSIC = ("classic", "레스토랑 목록을 불러오는 기본 방식")
    SEARCH = ("search", "검색을 통해 레스토랑 목록을 불러오는 방식")
    CLASSIC_MAP = ("classic_map", "레스토랑 목록을 불러오는 기본 방식 (Map View)")
    MART_HOME = ("mart_home", "dmart 서브홈으로 이동하는 방식")
    DEEPLINK = ("deeplink", "딥링크 URL")


class HomeCategoryListViewType(StrLabelPairEnum):
    BASIC = ("basic", "기본 레스토랑 목록 형식")
    PANORAMA = ("panorama", "썸네일 이미지와 함께 보여지는 레스토랑 목록 형식")


class FunctionalCategoryImagesPositions(StrLabelPairEnum):
    # _order_ = "IMAGE TITLE DOUBLE_LINE_DESCRIPTION SINGLE_LINE_DESCRIPTION IMAGE_SMALL IMAGE_LARGE"
    IMAGE = ("images", "아이콘 이미지")
    IMAGE_SMALL = ("image_small", "작은 아이콘 이미지 (6.14.0 이상)")
    IMAGE_LARGE = ("image_large", "큰 아이콘 이미지 (6.14.0 이상)")
    TITLE = ("title", "타이틀")
    SINGLE_LINE_DESCRIPTION = ("single_line_guide", "가이드 텍스트 (1줄)")
    DOUBLE_LINE_DESCRIPTION = ("double_line_guide", "가이드 텍스트 (2줄)")
    IMAGE_TITLE_M = ("image_title_m", "이미지 타이틀 M 사이즈")
    IMAGE_TITLE_S_UPPER = ("image_title_s_upper", "이미지 타이틀 S 사이즈 상단 정렬")
    IMAGE_TITLE_S_MID = ("image_title_s_mid", "이미지 타이틀 S 사이즈 가운데 정렬")


class HomeCategoryOrderServingType(StrLabelPairEnum):
    DELIVERY = ("delivery", "배달 주문")
    PICKUP = ("pickup", "포장 주문")
    PRE_ORDER_PICKUP = ("pre_order_pickup", "예약 픽업 주문 (시즌 한정)")


class HomeCategoryGtmShopListType(StrCodeEnum):
    NORMAL = "normal"
    CHAIN = "chain"
    TAKEOUT = "takeout"
    YGYEXPRESS = "ygyexpress"


class HomeCategoryManager(models.Manager):
    def get_query_set(self):
        return (
            super(HomeCategoryManager, self)
            .get_query_set()
            .exclude(is_deleted=True)
            .order_by("priority")
        )


class HomeCategoryListGroup(models.Model):
    name = models.CharField(
        max_length=20,
    )
    fwf_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Fun With Flags 에서 지정할 식별자",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="A/B 테스트 미진행시 기본으로 노출할 홈 카테고리 목록 그룹",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        default=None,
        db_index=False,
        help_text="그룹을 생성한 사용자",
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def clone_list(self, target_list_group):
        item_list = HomeCategory.fetch_active_list(list_group=self)

        with transaction.commit_on_success():
            for item in item_list:
                child_list = item.homecategory_set.all()
                image_list = item.image_set.all()
                cloned = item.clone(target_list_group)

                for child in child_list:
                    child.clone(target_list_group, cloned)

                for image in image_list:
                    image.clone(cloned)

    def delete_list(self):
        if self.is_default:
            raise SuspiciousOperation(
                "deleting default HomeCategory list is not allowed"
            )

        item_list = HomeCategory.objects.filter(list_group=self)
        child_list = HomeCategory.objects.filter(parent_category__in=item_list)
        image_list = HomeCategoryImage.objects.filter(home_category__in=item_list)

        with transaction.commit_on_success():
            image_list.delete()
            child_list.delete()
            item_list.delete()

    def __unicode__(self):
        return "{0.name} ({0.fwf_id})".format(self)

    class Meta:
        verbose_name_plural = "Home Category List Group (for A/B Test)"


class HomeCategory(models.Model):
    parent_category = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        default=None,
        help_text="상위 홈 카테고리",
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    # restaurant_category = models.ForeignKey(
    #     RestaurantCategory,
    #     null=True,
    #     blank=True,
    #     default=None,
    #     help_text="레스토랑 카테고리와의 연결 (위치 기반 표시/숨김 여부를 확인할 때 사용됩니다. 연결이 되어 있지 않을 경우 사용자 위치에 레스토랑 존재 여부 관계 없이 노출됩니다)",
    # )

    # restaurant_category 는 다음 2가지 필드만 필요합니다.
    # 타겟요로부터 restaurant_category slug 목록이 내려오면, 이것으로 available_by targetyo 를 호출합니다.
    restaurant_category_slug = models.CharField(max_length=200, null=True)

    # to_dict() 에서 restaurant_category_type 을 내려줄 때 활용합니다.
    restaurant_category_type = models.CharField(max_length=200, null=True)

    list_group = models.ForeignKey(
        HomeCategoryListGroup,
        null=True,
        blank=True,
        default=None,
        help_text="홈 카테고리가 포함될 목록 그룹 (A/B 테스트 그룹 설정 필요 시 변경, 생성 후 수정 불가능)",
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    display_name = models.CharField(
        max_length=20,
        help_text="화면에 표시되는 카테고리 이름",
    )
    priority = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(999),
        ],
        help_text="1~999, 우선순위가 높을수록 (숫자가 낮을수록) 목록에서 더 앞에 표시됩니다",
    )
    is_available_check_needed = models.BooleanField(
        default=False,
        help_text="위치 기반 표시/숨김 여부 (체크 시 사용자 위치에 레스토랑이 존재하지 않을 경우 숨김)",
    )
    list_view_type = models.CharField(
        max_length=100,
        choices=HomeCategoryListViewType.choices(),
        default=HomeCategoryListViewType.BASIC.value,
        help_text="레스토랑 목록의 화면 표시 방식",
    )
    order_serving_type = models.CharField(
        max_length=20,
        choices=HomeCategoryOrderServingType.choices(),
        default=HomeCategoryOrderServingType.DELIVERY.value,
        help_text="주문 방식 (배달/테이크아웃/예약 픽업)",
    )
    category_type = models.CharField(
        max_length=20,
        choices=HomeCategoryType.choices(),
        default=HomeCategoryType.DEFAULT.value,
        help_text="홈 카테고리 분류",
    )
    fetch_type = models.CharField(
        max_length=100,
        choices=HomeCategoryFetchType.choices(),
        help_text="레스토랑 목록을 불러오는 방식",
    )
    fetch_url = models.CharField(
        max_length=200,
        help_text="레스토랑 목록을 불러오는 API 경로",
    )
    min_required_ios_version = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default=None,
        help_text="지원하는 최소 iOS 앱 버전 (x.y.z, 테스트앱 버전 등 특수 케이스에 사용)",
    )
    min_required_android_version = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default=None,
        help_text="지원하는 최소 안드로이드 앱 버전 (x.y.z, 테스트앱 버전 등 특수 케이스에 사용)",
    )
    is_visible = models.BooleanField(
        default=False,
        help_text="화면 표시 여부 (체크 해제 시 화면에서 숨김)",
    )
    ga_name = models.CharField(
        max_length=200,
        verbose_name="GA Name",
        help_text="Google Analytics 에서 사용될 이름",
    )
    gtm_shop_list_type = models.CharField(
        max_length=20,
        verbose_name="GTM shopListType",
        choices=HomeCategoryGtmShopListType.choices(),
        default=HomeCategoryGtmShopListType.NORMAL.value,
        help_text="GTM shopListType 에 사용되는 값",
    )
    deeplink_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        default=None,
        help_text="모바일에서 딥링크 처리에 사용되는 값",
    )
    code = models.CharField(
        max_length=200,
        help_text="카테고리 고유 식별코드 (영문, 생성 후 수정 불가능)",
        validators=[
            RegexValidator(
                regex=r"(?i)^[a-z0-9]+([-_][a-z0-9]+)*$",
                message="영문, 숫자, 특수기호 (_, -) 만 입력 가능합니다. (예: hello_world-001)",
            ),
        ],
    )
    bg_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text="카테고리 백그라운드 색상 코드 (예: #FFFFFF)",
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = HomeCategoryManager()

    @property
    def is_mart_category(self):
        return self.code == settings.MART_HOME_CATEGORY_CODE

    @property
    def is_keyword_type(self):
        return self.category_type == HomeCategoryType.KEYWORD

    @property
    def is_function_type(self):
        return self.category_type == HomeCategoryType.FUNCTION

    def _filter_images(self):
        pre_filtered = [img for img in self.image_set.all() if img.image_url]

        now = datetime.now()
        event_images = [
            img
            for img in pre_filtered
            if img.is_event and img.event_starts_at <= now <= img.event_ends_at
        ]
        if event_images:
            return event_images
        return (img for img in pre_filtered if not img.is_event)

    def to_dict(self, fetch_url=None):
        filtered_image_objs = self._filter_images()
        images = [
            img.get_full_image_url()
            for img in sorted(filtered_image_objs, key=attrgetter("created_at"))
        ]  # 구버전 홈 카테고리 이미지를 하위 호환 하기 위해서 가장 오래된 이미지가 리스트의 맨 앞에 와야합니다.

        response = {
            "name": self.display_name,
            "list_view_type": self.list_view_type,
            "order_serving_type": self.order_serving_type,
            "fetch_type": self.fetch_type,
            "fetch_url": fetch_url or self.fetch_url,
            "ga_name": self.ga_name,
            "gtm_shop_list_type": self.gtm_shop_list_type,
            "code": self.code,
            "is_visible": self.is_visible,
            "deeplink_code": self.deeplink_code,
            "restaurant_category_type": (
                self.restaurant_category.category_type
                if self.fetch_type == HomeCategoryFetchType.CLASSIC
                and self.restaurant_category
                else None
            ),
            "images": images,
            "sub_categories": [
                {
                    "name": sub_item.display_name,
                    "list_view_type": sub_item.list_view_type,
                    "order_serving_type": sub_item.order_serving_type,
                    "fetch_type": sub_item.fetch_type,
                    "fetch_url": sub_item.fetch_url,
                    "ga_name": sub_item.ga_name,
                    "gtm_shop_list_type": sub_item.gtm_shop_list_type,
                    "code": sub_item.code,
                    "is_visible": sub_item.is_visible,
                    "deeplink_code": sub_item.deeplink_code,
                }
                for sub_item in sorted(
                    self.homecategory_set.all(), key=lambda e: e.priority
                )
                if not sub_item.is_deleted
            ],
        }
        if self.category_type == HomeCategoryType.FUNCTION:
            response["functional_images"] = {
                position: image
                for (position, _), image in zip(
                    FunctionalCategoryImagesPositions.choices(), images
                )
                if position != FunctionalCategoryImagesPositions.IMAGE.value
            }
            response["functional_images"][
                "guide_text"
            ] = HOME_CATEGORY_UI_GUIDE_TEXT.get(self.code)
            response["functional_images"]["bg_color"] = self.bg_color
        return response

    def clone(self, list_group, parent_category=None):
        """Clones by mutating current `self` object. But creates a new row in DB table.
        https://docs.djangoproject.com/en/3.0/topics/db/queries/#copying-model-instances"""
        self.list_group = list_group
        self.parent_category = parent_category
        self.pk = None
        self.save()

        return self

    def __unicode__(self):
        return "{0.display_name} ({0.code})".format(self)

    @classmethod
    def fetch_active_list(cls, list_group=None, exclude_fetch_type=None):
        # TODO: use Prefetch() for filtered & sorted prefetch after upgrading django >= 1.7 (PRE-202)
        qs = (
            cls.active.filter(parent_category=None)
            .select_related("restaurant_category")
            .prefetch_related("homecategory_set", "image_set")
        )

        if list_group:
            qs = qs.filter(list_group=list_group)
        else:
            qs = qs.filter(list_group__is_default=True)

        if exclude_fetch_type:
            qs = qs.exclude(fetch_type__in=exclude_fetch_type)

        return qs

    class Meta:
        verbose_name_plural = "Home Categories"
        unique_together = (
            ("list_group", "parent_category", "deeplink_code"),
            ("list_group", "code"),
        )


class HomeCategoryImage(models.Model):
    home_category = models.ForeignKey(
        HomeCategory,
        related_name="image_set",
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    is_deprecated = models.BooleanField(
        default=True,
        help_text="구버전에서 사용할 기본 이미지",
    )
    image_url = models.FileField(
        max_length=200,
        upload_to=DETAIL_IMAGE_S3_UPLOAD_DIR,
        storage=S3_REVIEW_IMAGE_BUCKET_STORAGE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # event home category 만 갖는 필드.
    is_event = models.BooleanField(default=False, help_text="이벤트용 홈 카테고리 이미지")
    event_starts_at = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
        help_text="이벤트용 홈 카테고리 이미지의 시작 시간",
    )
    event_ends_at = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
        help_text="이벤트용 홈 카테고리 이미지의 종료 시간",
    )

    def get_full_image_url(self):
        return get_s3_review_image_bucket_url(self.image_url.name)

    def clone(self, home_category):
        """Clones by mutating current `self` object. But creates a new row in DB table.
        https://docs.djangoproject.com/en/3.0/topics/db/queries/#copying-model-instances"""
        self.home_category = home_category
        self.pk = None
        self.save()

        return self
