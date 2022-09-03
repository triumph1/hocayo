from datetime import datetime

from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.forms.models import BaseInlineFormSet
from dowant.halpers.enums import StrLabelPairEnum
from dowant.home_category.consts import FUNCTION_CATEGORY_IMG_COUNT
from dowant.home_category.helpers import (
    validate_home_category_icon_image_filesize,
    validate_home_category_icon_image_filetype,
    validate_home_category_icon_image_size,
    validate_home_category_icon_lottie_filetype)
from dowant.settings.s3utils import upload_image_to_s3

from home_category.models import (HomeCategory, HomeCategoryFetchType,
                                  HomeCategoryImage, HomeCategoryListGroup,
                                  HomeCategoryType)


class HomeCategoryClassicDeliveryType(StrLabelPairEnum):
    ALL = ("", "전체")
    OD_ONLY = ("own_delivery_only", "요기요 익스프레스 매장만 포함 (own_delivery_only)")


class HomeCategoryImageType(StrLabelPairEnum):
    IMAGE = ("image_file", "이미지 파일")
    LOTTIE = ("lottie_file", "Lottie JSON 파일")


HOME_CATEGORY_ICON_UPLOAD_DIRS = {
    HomeCategoryImageType.IMAGE: "home_categories/images",
    HomeCategoryImageType.LOTTIE: "home_categories/lottie_files",
}
HOME_CATEGORY_CLASSIC_CATEGORY_CHOICES = [
    ("전체", "전체"),
    ("찜탕", "찜탕"),
    ("분식", "분식"),
    ("야식", "야식"),
    ("중식", "중식"),
    ("치킨", "치킨"),
    ("한식", "한식"),
    ("버거", "버거"),
    ("샌드위치", "샌드위치"),
    ("회초밥", "회초밥"),
    ("도시락죽", "도시락죽"),
    ("샐러드", "샐러드"),
    ("아시안", "아시안"),
    ("고기구이", "고기구이"),
    ("편의점", "편의점"),
    ("예약픽업", "예약픽업"),
    ("족발보쌈", "족발보쌈"),
    ("피자양식", "피자양식"),
    ("1인분주문", "1인분주문"),
    ("일식돈까스", "일식돈까스"),
    ("카페디저트", "카페디저트"),
    ("테이크아웃", "테이크아웃"),
    ("프랜차이즈", "프랜차이즈"),
    ("반려동물용품", "반려동물용품"),
    ("헬스뷰티", "헬스뷰티"),
    ("밀키트", "밀키트"),
    ("다회용기", "다회용기"),
    ("신규맛집", "신규맛집"),
    ("요기픽", "요기픽"),
    ("리빙라이프", "리빙라이프"),
]


class HomeCategoryForm(forms.ModelForm):
    classic_category = forms.ChoiceField(
        label="Category",
        choices=HOME_CATEGORY_CLASSIC_CATEGORY_CHOICES,
        required=False,
    )
    classic_order = forms.CharField(
        label="Order",
        max_length=20,
        required=False,
        help_text="[DEPRECATED] 더 이상 사용되지 않는 입력 필드입니다.",
    )
    classic_delivery_type = forms.ChoiceField(
        label="Delivery Type",
        choices=HomeCategoryClassicDeliveryType.choices(),
        required=False,
    )
    search_keyword = forms.CharField(
        label="Keyword",
        max_length=20,
        required=False,
    )
    deeplink_fetch_url = forms.CharField(
        label="Deep Link",
        max_length=80,
        required=False,
    )
    display_name = forms.CharField(
        max_length=6,
        help_text="화면에 표시되는 카테고리 이름 (최대 6자)",
    )
    list_group = forms.ModelChoiceField(
        queryset=HomeCategoryListGroup.objects.order_by("-is_default"),
        empty_label=None,
        required=False,
        help_text="홈 카테고리가 포함될 목록 그룹 (A/B 테스트 그룹 설정 필요 시 변경, 생성 후 수정 불가능)",
    )

    def __init__(self, *args, **kwargs):
        super(HomeCategoryForm, self).__init__(*args, **kwargs)

        self.fields["classic_order"].initial = (
            self.fields["classic_order"].initial or "rank"
        )

    def clean_code(self):
        value = self.cleaned_data.get("code")

        if self.instance and self.instance.pk and self.instance.code != value:
            raise forms.ValidationError("카테고리 코드는 생성 후 수정이 불가능합니다.")
        return value

    def clean_fetch_type(self):
        category_type = self.cleaned_data.get("category_type")
        fetch_type = self.cleaned_data.get("fetch_type")

        if (
            fetch_type == HomeCategoryFetchType.SEARCH
            and category_type != HomeCategoryType.KEYWORD
        ):
            raise forms.ValidationError("검색을 통한 레스토랑 호출은 KEYWORD 카테고리에서만 가능합니다.")
        return fetch_type

    class Meta:
        model = HomeCategory


class HomeCategoryImageForm(forms.ModelForm):
    image_type = forms.ChoiceField(
        label="파일 유형",
        choices=HomeCategoryImageType.choices(),
        required=False,
    )
    image_file = forms.ImageField(
        label="새로운 이미지 파일",
        required=False,
    )
    lottie_file = forms.FileField(
        label="새로운 Lottie JSON 파일",
        required=False,
    )
    image_url = forms.FileField(
        label="현재 이미지 경로",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(HomeCategoryImageForm, self).__init__(*args, **kwargs)
        self.is_event = False

    def clean(self):
        cleaned_data = super(HomeCategoryImageForm, self).clean()
        image_type = cleaned_data.get("image_type")
        field_file = cleaned_data.get(image_type)
        file_ = self.files.get("{}-{}".format(self.prefix, image_type))

        if field_file and file_:
            try:
                if image_type == HomeCategoryImageType.IMAGE.value:
                    validate_home_category_icon_image_filetype(field_file)
                    validate_home_category_icon_image_filesize(field_file)
                    validate_home_category_icon_image_size(field_file)
                else:
                    validate_home_category_icon_lottie_filetype(field_file)
            except forms.ValidationError as err:
                self._errors.setdefault(image_type, self.error_class()).extend(
                    self.error_class(err.messages),
                )

            if not self._errors.get(image_type):
                cleaned_data["image_url"] = field_file
                self.files["{}-image_url".format(self.prefix)] = file_

        return cleaned_data

    class Meta:
        model = HomeCategoryImage


class EventHomeCategoryImageForm(HomeCategoryImageForm):
    event_starts_at = forms.DateTimeField(
        label="시작 시각",
        required=True,
        widget=AdminSplitDateTime(),
    )
    event_ends_at = forms.DateTimeField(
        label="종료 시각",
        required=True,
        widget=AdminSplitDateTime(),
    )

    def __init__(self, *args, **kwargs):
        """
        home category image form set 에서
        obj.is_event = form.is_event 를 한다.
        """
        super(EventHomeCategoryImageForm, self).__init__(*args, **kwargs)
        self.is_event = True

    def clean(self):
        cleaned_data = super(EventHomeCategoryImageForm, self).clean()

        event_starts_at = self.cleaned_data.get("event_starts_at")
        event_ends_at = self.cleaned_data.get("event_ends_at")
        if event_starts_at and event_ends_at and event_starts_at > event_ends_at:
            msg = "종료시간은 시작시간보다 나중이어야 합니다."
            self._errors["event_starts_at"] = self.error_class([msg])
            self._errors["event_ends_at"] = self.error_class([msg])

        return cleaned_data


class HomeCategoryImageInlineFormset(BaseInlineFormSet):
    def clean(self):
        super(HomeCategoryImageInlineFormset, self).clean()

        if self.data["category_type"] == HomeCategoryType.KEYWORD:
            return

        if not self.forms:
            raise forms.ValidationError("이미지를 등록해주세요.")

        for form in self.forms:
            if form in self.extra_forms and not self._is_actual_changed(
                form.changed_data
            ):
                if self.data["category_type"] == HomeCategoryType.FUNCTION:
                    raise forms.ValidationError(
                        "기능 카테고리는 {}개 이미지를 모두 등록해주세요.".format(
                            FUNCTION_CATEGORY_IMG_COUNT
                        )
                    )
            elif hasattr(self, "deleted_forms") and form in self.deleted_forms:
                if self.data["category_type"] == HomeCategoryType.FUNCTION:
                    raise forms.ValidationError("기능 카테고리 이미지를 삭제할 수 없습니다.")

    def _is_deleted_all_images(self):
        # initial_forms(기존 이미지) + extra_forms(추가 이미지) <= deleted_forms(삭제 이미지)
        return len(self.initial_forms) + len(self.extra_forms) <= len(
            self.deleted_forms
        )

    def _is_actual_changed(self, changed_data):
        # changed_data는 항상 image_type을 포함하고 있어, 실질적으로 변경되지 않은 form를 구분하기 위함
        return not (len(changed_data) == 1 and changed_data[0] == "image_type")

    def save_new_objects(self, commit=True):
        self.new_objects = []
        for form in self.extra_forms:
            if not form.has_changed():
                continue
            # If someone has marked an add form for deletion, don't save the
            # object.
            if (
                self.can_delete and self._should_delete_form(form)
            ) or not self._is_actual_changed(form.changed_data):
                continue
            self.new_objects.append(self.save_new(form, commit=commit))
            if not commit:
                self.saved_forms.append(form)
        return self.new_objects

    def save_new(self, form, commit=True):
        obj = super(HomeCategoryImageInlineFormset, self).save_new(form, commit=False)
        obj.is_event = form.is_event
        return self._save_home_category_image(form, obj, commit)

    def save_existing(self, form, instance, commit=True):
        obj = super(HomeCategoryImageInlineFormset, self).save_existing(
            form, instance, commit=False
        )
        return self._save_home_category_image(form, obj, commit)

    @staticmethod
    def _save_home_category_image(form, obj, commit):
        image = form.files.get("{}-image_url".format(form.prefix))

        if image:
            image_type = (
                HomeCategoryImageType.IMAGE
                if image.content_type == "image/png"
                else HomeCategoryImageType.LOTTIE
            )
            filename = "{:%Y%m%d%H%M%S%f}_{}".format(
                datetime.now(),
                image.name,
            )
            s3_path = upload_image_to_s3(
                HOME_CATEGORY_ICON_UPLOAD_DIRS[image_type], image, filename
            )
            obj.image_url = s3_path

        if commit:
            obj.save()
        return obj


class EventHomeCategoryImageInlineFormset(HomeCategoryImageInlineFormset):
    def clean(self):
        """
        HomeCategoryImageInlineFormset 의 clean 은 form 이 하나도 없으면 유효하지 않습니다.
        하지만 이벤트 홈 카테고리는 아무것도 없는 상태도 얼마든지 가능합니다.
        따라서 재정의합니다. 단, 새 form 을 이미지 없이 제출하는 경우는 ValidationError 를 일으킵니다.
        """

        super(HomeCategoryImageInlineFormset, self).clean()

        for form in self.extra_forms:
            if form.is_valid() and not (
                form.cleaned_data["image_file"] or form.cleaned_data["lottie_file"]
            ):
                raise forms.ValidationError("이미지나 lottie 중 하나 이상을 등록하셔야 합니다.")


class HomeCategoryListGroupForm(forms.ModelForm):
    clone_from = forms.ModelChoiceField(
        queryset=HomeCategoryListGroup.objects.order_by("-is_default"),
        empty_label=None,
        required=False,
        help_text="복제할 대상 목록 그룹 (선택한 목록 그룹으로부터 복제된 홈 카테고리 목록이 생성됩니다)",
    )

    class Meta:
        model = HomeCategoryListGroup
