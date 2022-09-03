from django.contrib import admin
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe

from home_category.consts import HOME_CATEGORY_ADMIN_NOTICE
from home_category.forms import (EventHomeCategoryImageForm,
                                 EventHomeCategoryImageInlineFormset,
                                 HomeCategoryForm, HomeCategoryImageForm,
                                 HomeCategoryImageInlineFormset,
                                 HomeCategoryListGroupForm)
from home_category.models import (FunctionalCategoryImagesPositions,
                                  HomeCategory, HomeCategoryImage,
                                  HomeCategoryListGroup)

IMAGE_TEMPLATE = """
<a href="{url}" target="_blank">
    <img src="{url}" height="100"/>
</a>
"""
LOTTIE_PLAYER_TEMPLATE = """
<a href="{url}" target="_blank">
    <lottie-player
        src="{url}"
        background="transparent"
        speed="1"
        style="width: 100px; height: 100px;"
        loop
        autoplay
    />
</a>
"""


class RelatedOnlyFieldListFilter(admin.RelatedFieldListFilter):
    # ref: https://github.com/django/django/blob/stable/1.4.x/django/contrib/admin/filters.py#L191
    def choices(self, cl):
        for pk_val, val in self.lookup_choices:
            yield {
                "selected": self.lookup_val == smart_str(pk_val),
                "query_string": cl.get_query_string(
                    {
                        self.lookup_kwarg: pk_val,
                    },
                    [self.lookup_kwarg_isnull],
                ),
                "display": val,
            }


class HomeCategoryImageInline(admin.TabularInline):
    template = "admin/home_category/edit_inline/tabular.html"
    line_numbering = 0
    formset = HomeCategoryImageInlineFormset
    form = HomeCategoryImageForm
    model = HomeCategoryImage
    extra = 9
    max_num = 9
    verbose_name_plural = "신규버전 홈 카테고리 아이콘 이미지 목록"
    verbose_name = "신규버전 홈 카테고리 아이콘 이미지"
    notice = mark_safe(HOME_CATEGORY_ADMIN_NOTICE)
    readonly_fields = ("image_url", "s3_image", "image_position")
    fields = (
        "image_position",
        "image_url",
        "s3_image",
        "image_type",
        "image_file",
        "lottie_file",
    )

    def queryset(self, request):
        qs = super(HomeCategoryImageInline, self).queryset(request)
        return qs.filter(is_event=False)

    def image_position(self, obj):
        label = (
            FunctionalCategoryImagesPositions.choices()[self.line_numbering][1]
            if self.line_numbering < self.max_num
            else "노출되지 않음"
        )
        self.line_numbering += 1
        return label

    image_position.short_description = "이미지 노출 영역"

    def s3_image(self, obj):
        if obj.image_url:
            s3_url = obj.get_full_image_url()

            if s3_url.lower().endswith(".json"):
                return mark_safe(LOTTIE_PLAYER_TEMPLATE.format(url=s3_url))
            return mark_safe(IMAGE_TEMPLATE.format(url=s3_url))
        return "-"

    s3_image.short_description = "현재 이미지 파일"


class EventHomeCategoryImageInline(HomeCategoryImageInline):
    form = EventHomeCategoryImageForm
    formset = EventHomeCategoryImageInlineFormset
    verbose_name_plural = "신규버전 홈 카테고리 아이콘 (이벤트용)"
    verbose_name = "신규버전 홈 카테고리 아이콘 (이벤트용)"
    extra = 0
    notice = mark_safe(
        """
        <strong>[ 이미지 사이즈 ]</strong><br>
        - 아이콘 이미지 : 204 x 204
        """
    )

    fields = (
        "image_position",
        "event_starts_at",
        "event_ends_at",
        "image_url",
        "s3_image",
        "image_type",
        "image_file",
        "lottie_file",
    )

    def image_position(self, obj):
        return FunctionalCategoryImagesPositions.IMAGE.label

    def queryset(self, request):
        qs = super(HomeCategoryImageInline, self).queryset(request)
        return qs.filter(is_event=True)


class SubHomeCategoryInline(admin.StackedInline):
    form = HomeCategoryForm
    model = HomeCategory
    extra = 0
    verbose_name_plural = "하위 홈 카테고리 목록"
    verbose_name = "하위 홈 카테고리"
    ordering = ("priority",)
    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "display_name",
                    "priority",
                    "order_serving_type",
                    "is_visible",
                    "ga_name",
                    "gtm_shop_list_type",
                    "deeplink_code",
                    "code",
                    "bg_color",
                ),
            },
        ),
        (
            "레스토랑 목록을 불러오는 방식",
            {
                "fields": (
                    "fetch_type",
                    "fetch_url",
                    "classic_category",
                    "classic_delivery_type",
                    "classic_order",
                    "search_keyword",
                ),
            },
        ),
    )


class HomeCategoryAdmin(admin.ModelAdmin):
    form = HomeCategoryForm
    list_display = (
        "category_type",
        "display_name",
        "list_group",
        "priority",
        "is_visible",
        "is_deleted",
        "created_at",
        "modified_at",
    )
    list_display_links = ("display_name",)
    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "id",
                    "list_group",
                    "display_name",
                    "restaurant_category",
                    "category_type",
                    "priority",
                    "order_serving_type",
                    "is_available_check_needed",
                    "is_visible",
                    "is_deleted",
                    "ga_name",
                    "gtm_shop_list_type",
                    "deeplink_code",
                    "min_required_android_version",
                    "min_required_ios_version",
                    "code",
                    "bg_color",
                ),
            },
        ),
        (
            "레스토랑 목록을 불러오는 방식",
            {
                "fields": (
                    "fetch_type",
                    "fetch_url",
                    "classic_category",
                    "classic_delivery_type",
                    "classic_order",
                    "deeplink_fetch_url",
                    "search_keyword",
                ),
            },
        ),
    )
    readonly_fields = ("is_deleted", "id")
    ordering = ("is_deleted", "priority")
    inlines = (
        HomeCategoryImageInline,
        EventHomeCategoryImageInline,
        SubHomeCategoryInline,
    )
    list_filter = (
        "category_type",
        ("list_group", RelatedOnlyFieldListFilter),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("list_group",)
        return super(HomeCategoryAdmin, self).get_readonly_fields(request, obj)

    def changelist_view(self, request, extra_context=None):
        q = request.GET.copy()

        # display only root home categories
        if "parent_category__isnull" not in q:
            q["parent_category__isnull"] = "True"

        if "list_group__id__exact" not in q:
            default_group = HomeCategoryListGroup.objects.get(is_default=True)
            q["list_group__id__exact"] = default_group.pk

        request.GET = q
        request.META["QUERY_STRING"] = request.GET.urlencode()

        return super(HomeCategoryAdmin, self).changelist_view(
            request, extra_context=extra_context
        )

    def save_formset(self, request, form, formset, change):
        instance_list = formset.save()

        # set list_group of child home categories
        for instance in instance_list:
            if hasattr(instance, "list_group"):
                instance.list_group = form.instance.list_group
                instance.save()

    def delete_model(self, request, obj):
        if request.method == "POST":
            obj.is_deleted = True
            obj.save()
            return
        return super(HomeCategoryAdmin, self).delete_model(request, obj)

    class Media:
        js = (
            "/media/js/lib/underscore/underscore.js",
            "/media/js/backend/home_category_admin.js",
            "/media/js/backend/home_category_image_admin.js",
            "/media/js/backend/form.js",
            # v0.5.1 lottie animation player
            # NOTE: version can be changed if needed
            "https://unpkg.com/@lottiefiles/lottie-player@0.5.1/dist/lottie-player.js",
        )


admin.site.register(HomeCategory, HomeCategoryAdmin)


class HomeCategoryListGroupAdmin(admin.ModelAdmin):
    form = HomeCategoryListGroupForm
    list_display = (
        "name",
        "fwf_id",
        "is_default",
        "created_by",
        "created_at",
        "modified_at",
        "home_category_list_link",
    )
    fields = (
        "name",
        "fwf_id",
        "is_default",
        "home_category_list_link",
    )
    readonly_fields = ("is_default", "created_by", "home_category_list_link")
    ordering = ("-is_default",)

    def home_category_list_link(self, obj):
        if not (obj and obj.pk):
            return "-"
        path = "/admin/home_category/homecategory/?list_group__id__exact={}".format(
            obj.pk
        )
        return '<a href="{}">홈 카테고리 목록으로 이동</a>'.format(path)

    home_category_list_link.short_description = "홈 카테고리 목록"
    home_category_list_link.allow_tags = True

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return ((None, {"fields": self.fields + ("clone_from",)}),)
        return super(HomeCategoryListGroupAdmin, self).get_fieldsets(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_default:
            return False
        return super(HomeCategoryListGroupAdmin, self).has_delete_permission(
            request, obj
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        result = super(HomeCategoryListGroupAdmin, self).save_model(
            request, obj, form, change
        )

        if change:
            return result

        clone_from = form.cleaned_data["clone_from"]
        clone_from.clone_list(obj)
        return result

    def delete_model(self, request, obj):
        obj.delete_list()
        return super(HomeCategoryListGroupAdmin, self).delete_model(request, obj)

    class Media:
        js = ("/media/js/backend/form.js",)


admin.site.register(HomeCategoryListGroup, HomeCategoryListGroupAdmin)
