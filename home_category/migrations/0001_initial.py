# Generated by Django 4.1 on 2022-09-03 03:50

import django.core.files.storage
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HomeCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("restaurant_category_slug", models.CharField(max_length=200)),
                ("restaurant_category_type", models.CharField(max_length=200)),
                (
                    "display_name",
                    models.CharField(help_text="화면에 표시되는 카테고리 이름", max_length=20),
                ),
                (
                    "priority",
                    models.PositiveIntegerField(
                        help_text="1~999, 우선순위가 높을수록 (숫자가 낮을수록) 목록에서 더 앞에 표시됩니다",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(999),
                        ],
                    ),
                ),
                (
                    "is_available_check_needed",
                    models.BooleanField(
                        default=False,
                        help_text="위치 기반 표시/숨김 여부 (체크 시 사용자 위치에 레스토랑이 존재하지 않을 경우 숨김)",
                    ),
                ),
                (
                    "list_view_type",
                    models.CharField(
                        choices=[
                            ("basic", "기본 레스토랑 목록 형식"),
                            ("panorama", "썸네일 이미지와 함께 보여지는 레스토랑 목록 형식"),
                        ],
                        default="basic",
                        help_text="레스토랑 목록의 화면 표시 방식",
                        max_length=100,
                    ),
                ),
                (
                    "order_serving_type",
                    models.CharField(
                        choices=[
                            ("delivery", "배달 주문"),
                            ("pickup", "포장 주문"),
                            ("pre_order_pickup", "예약 픽업 주문 (시즌 한정)"),
                        ],
                        default="delivery",
                        help_text="주문 방식 (배달/테이크아웃/예약 픽업)",
                        max_length=20,
                    ),
                ),
                (
                    "category_type",
                    models.CharField(
                        choices=[
                            ("default", "음식"),
                            ("keyword", "키워드"),
                            ("function", "기능"),
                        ],
                        default="default",
                        help_text="홈 카테고리 분류",
                        max_length=20,
                    ),
                ),
                (
                    "fetch_type",
                    models.CharField(
                        choices=[
                            ("classic", "레스토랑 목록을 불러오는 기본 방식"),
                            ("search", "검색을 통해 레스토랑 목록을 불러오는 방식"),
                            ("classic_map", "레스토랑 목록을 불러오는 기본 방식 (Map View)"),
                            ("mart_home", "dmart 서브홈으로 이동하는 방식"),
                            ("deeplink", "딥링크 URL"),
                        ],
                        help_text="레스토랑 목록을 불러오는 방식",
                        max_length=100,
                    ),
                ),
                (
                    "fetch_url",
                    models.CharField(help_text="레스토랑 목록을 불러오는 API 경로", max_length=200),
                ),
                (
                    "min_required_ios_version",
                    models.CharField(
                        blank=True,
                        default=None,
                        help_text="지원하는 최소 iOS 앱 버전 (x.y.z, 테스트앱 버전 등 특수 케이스에 사용)",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "min_required_android_version",
                    models.CharField(
                        blank=True,
                        default=None,
                        help_text="지원하는 최소 안드로이드 앱 버전 (x.y.z, 테스트앱 버전 등 특수 케이스에 사용)",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "is_visible",
                    models.BooleanField(
                        default=False, help_text="화면 표시 여부 (체크 해제 시 화면에서 숨김)"
                    ),
                ),
                (
                    "ga_name",
                    models.CharField(
                        help_text="Google Analytics 에서 사용될 이름",
                        max_length=200,
                        verbose_name="GA Name",
                    ),
                ),
                (
                    "gtm_shop_list_type",
                    models.CharField(
                        choices=[
                            ("normal", "normal"),
                            ("chain", "chain"),
                            ("takeout", "takeout"),
                            ("ygyexpress", "ygyexpress"),
                        ],
                        default="normal",
                        help_text="GTM shopListType 에 사용되는 값",
                        max_length=20,
                        verbose_name="GTM shopListType",
                    ),
                ),
                (
                    "deeplink_code",
                    models.CharField(
                        blank=True,
                        default=None,
                        help_text="모바일에서 딥링크 처리에 사용되는 값",
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="카테고리 고유 식별코드 (영문, 생성 후 수정 불가능)",
                        max_length=200,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="영문, 숫자, 특수기호 (_, -) 만 입력 가능합니다. (예: hello_world-001)",
                                regex="(?i)^[a-z0-9]+([-_][a-z0-9]+)*$",
                            )
                        ],
                    ),
                ),
                (
                    "bg_color",
                    models.CharField(
                        blank=True,
                        help_text="카테고리 백그라운드 색상 코드 (예: #FFFFFF)",
                        max_length=7,
                        null=True,
                    ),
                ),
                ("is_deleted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "Home Categories",
            },
        ),
        migrations.CreateModel(
            name="HomeCategoryListGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20)),
                (
                    "fwf_id",
                    models.CharField(
                        help_text="Fun With Flags 에서 지정할 식별자",
                        max_length=50,
                        unique=True,
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False, help_text="A/B 테스트 미진행시 기본으로 노출할 홈 카테고리 목록 그룹"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        db_index=False,
                        default=None,
                        help_text="그룹을 생성한 사용자",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Home Category List Group (for A/B Test)",
            },
        ),
        migrations.CreateModel(
            name="HomeCategoryImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_deprecated",
                    models.BooleanField(default=True, help_text="구버전에서 사용할 기본 이미지"),
                ),
                (
                    "image_url",
                    models.FileField(
                        max_length=200,
                        storage=django.core.files.storage.FileSystemStorage(
                            base_url="https://dev-rev-static.yogiyo.co.kr", location=""
                        ),
                        upload_to="restaurants/detail_image",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "is_event",
                    models.BooleanField(default=False, help_text="이벤트용 홈 카테고리 이미지"),
                ),
                (
                    "event_starts_at",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text="이벤트용 홈 카테고리 이미지의 시작 시간",
                        null=True,
                    ),
                ),
                (
                    "event_ends_at",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text="이벤트용 홈 카테고리 이미지의 종료 시간",
                        null=True,
                    ),
                ),
                (
                    "home_category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="image_set",
                        to="home_category.homecategory",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="homecategory",
            name="list_group",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text="홈 카테고리가 포함될 목록 그룹 (A/B 테스트 그룹 설정 필요 시 변경, 생성 후 수정 불가능)",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="home_category.homecategorylistgroup",
            ),
        ),
        migrations.AddField(
            model_name="homecategory",
            name="parent_category",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text="상위 홈 카테고리",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="home_category.homecategory",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="homecategory",
            unique_together={
                ("list_group", "code"),
                ("list_group", "parent_category", "deeplink_code"),
            },
        ),
    ]
