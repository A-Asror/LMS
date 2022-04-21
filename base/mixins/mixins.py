from django.conf import settings
from django.core.cache import cache
# from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework import status
from rest_framework.generics import GenericAPIView

# from base.views.custom_generics import BaseView
# from myapp.models import SubComments
# from myapp.serializers import CommentsSerialize, SubCommentsSerialize
from account.models import User


class BaseMixin(GenericAPIView):
    error_data = {'data': 'no valid data'}
    error = {'error': 'no data to ID'}
    error_code = status.HTTP_400_BAD_REQUEST
    serializer_context = {}
    filter_data = {}
    order_by = '-pk'
    func = 1
    _filter = True
    cache_data = None

    def valid_data(self, data):
        return False if not data else True

    @property
    def validation_context_and_filter(self):
        if self.func:
            return dict() if not len(self.serializer_context) else self.serializer_context
        return dict() if not len(self.filter_data) else self.filter_data

    def retrieve(self, data):
        self.func = True
        if self.valid_data(data):
            serializer = self.get_serializer(data, context=self.validation_context_and_filter)
            return serializer.data, status.HTTP_200_OK
        else:
            return self.error, status.HTTP_400_BAD_REQUEST

    def retrieve_many(self, data):
        self.func = True
        if self.valid_data(data):
            serializer = self.get_serializer(data, context=self.validation_context_and_filter, many=True)
            return serializer.data, status.HTTP_200_OK
        else:
            return self.error, status.HTTP_400_BAD_REQUEST

    @property
    def get_object(self):
        # self.cached()
        # if self.cache_data is not None:
        #     return self.cache_data
        data = self.queryset.objects.filter(**self.validation_context_and_filter)
        if not self._filter and data.exists():
            obj = data.get()
            self.check_object_permissions(self.request, obj)
            return obj
        elif data.exists():
            data = data.order_by(self.order_by)
            return data
        return False
        # return data.get() if not self._filter and data.exists() else False if data.exists() else data

    # cache_data = cache.get(str(pk))
    # if cache_data:
    #     print(cache_data)
    #     data, status_code = self.retrieve(cache_data)
    #     return data, status_code

    # if cache.get(str(pk)) is None:
    # cache.add(str(pk), 'HELLO', 60*24)

    @property
    def retrieve_or_all(self):
        self.func = False
        filter_data = self.validation_context_and_filter
        pk = self.kwargs.get('pk', None)
        if pk is not None:
            self._filter = False
            filter_data['pk'] = pk
            self.filter_data['pk'] = pk
            # self.filter_data = filter_data
        if len(self.filter_data):
            data = self.get_object
            # if self.cache_data is not None:
            #     return data, 200
            if self.valid_data(data):
                if len(self.filter_data) >= 1 and not 'pk' in self.filter_data.keys():
                    data, status_code = self.retrieve_many(data)
                else:
                    data, status_code = self.retrieve(data)
                # self.cached(data, False)
                return data, status_code
            return self.error, self.error_code
        else:
            # self.cached()
            # if self.cache_data is not None:
            #     return self.cache_data, 200
            self.func = True
            data = User.objects.all().order_by(self.order_by)
            # print(data)
            serializer = self.serializer_class(data, many=True, context=self.validation_context_and_filter)  # , context={'many': True, 'queryset': obj}
            # self.cached(serializer.data, get=False)
            return serializer.data, status.HTTP_200_OK

    def cached(self, data=None, get=True):
        key = self.queryset.__name__ + str(self.filter_data)
        if get:
            self.cache_data = cache.get(key)
            return self.cache_data
        cache.set(key, data)
        # print(key)


class CustomUpdateMixin(BaseMixin):

    def update(self, instance, data):
        if self.valid_data(instance):
            self.func = 1
            serializer = self.get_serializer(instance, data=data, partial=True, context=self.validation_context_and_filter)
            if serializer.is_valid(raise_exception=False):
                serializer.save()
                return serializer.data, status.HTTP_200_OK
            else:
                return serializer.errors, status.HTTP_400_BAD_REQUEST
        return self.error, self.error_code


class CustomDestroyModelMixin(BaseMixin):

    def destroy(self, pk):
        obj = self.get_object
        if obj:
            obj.delete()
            return {'success': 'deleted'}, 200
        return {'error': f'no data to pk: {pk}'}, 400


class CustomCreateMixin(BaseMixin):

    def create(self, data):
        serializer = self.get_serializer(data=data, context=self.validation_context_and_filter)
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            return serializer.data, status.HTTP_201_CREATED
        return serializer.errors, status.HTTP_400_BAD_REQUEST
