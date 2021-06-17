import datetime
from datetime import date
from datetime import datetime
from operator import itemgetter

from dateutil import relativedelta

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db.models.functions import Length, TruncDate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, views
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializer import *
from .models import *
from appointments.models import *
from labResults.models import *


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def restricted(request, *args, **kwargs):
    return Response(data="ffff")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        # This data variable will contain refresh and access tokens
        data = super().validate(attrs)
        # You can add more User model's attributes like username,email etc. in the data dictionary like this.
        data['data'] = {'CCCNo': self.user.CCCNo, 'msisdn': self.user.msisdn}
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileListCreateView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def depend(request):
    if request.method == 'POST':
        data_copy = request.data.copy()
        data_copy.update({"user": request.user.id})
        serializer = DependantSerializer(data=data_copy)
        serializer.user = request.user
        print(serializer.is_valid())
        try:
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "error": 'something went wrong'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        queryset = Dependants.objects.filter(user=request.user.id)
        serializer = DependantSerializer(queryset, many=True)
        today = date.today()
        for d in serializer.data:
            dob = d["dob"]
            date1 = datetime.strptime(str(dob), '%Y-%m-%d')
            date2 = datetime.strptime(str(today), '%Y-%m-%d')
            r = relativedelta.relativedelta(date2, date1)
            months_difference = r.months + (12 * r.years)
            d["dob"] = months_difference
        return Response(data={"data": serializer.data}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def signup(request):
    if request.method == 'POST':
        # TODO signup for dependants is active
        data_copy = request.data.copy()
        a = check_ccc(request.data['CCCNo'])
        if a == False:
            return Response({"success": False, "error": "Invalid CCC number"}, status=status.HTTP_400_BAD_REQUEST)
        print(type(check_ccc(request.data['CCCNo'])['f_name']))
        data_copy.update({"first_name": check_ccc(request.data['CCCNo'])["f_name"]})
        data_copy.update({"last_name": check_ccc(request.data['CCCNo'])["l_name"]})
        data_copy.update({"initial_facility": check_ccc(request.data['CCCNo'])["mfl_code"]})
        data_copy.update({"current_facility": check_ccc(request.data['CCCNo'])["mfl_code"]})

        serializer = UserSerializer(data=data_copy)
        if not serializer.is_valid():
            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.initial_data['password'] != serializer.initial_data['re_password']:
            raise serializers.ValidationError("Passwords don't match")
        try:
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True,
                                 "data": {
                                     "user": "User Created"
                                 }},
                                status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"success": False, "error": [serializer.errors, str(e)]},
                            status=status.HTTP_400_BAD_REQUEST)


def check_ccc(value):
    user = {
        "ccc_number": value
    }

    url = "http://ushaurinode.mhealthkenya.org/api/mlab/get/one/client"
    headers = {
        'content-type': "application/json",
        'Accept': 'application/json'
    }
    response = requests.post(url, data=user, json=headers)
    try:
        return response.json()["clients"][0]
    except IndexError:
        return False


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_auth_user(request):
    if request.method == 'GET':
        queryset = User.objects.filter(id=request.user.id)
        dep = Dependants.objects.filter(user=request.user)
        reg = Regiment.objects.filter(user=request.user).order_by('-date_started').first()
        dep_serializer = DependantSerializer(dep, many=True)
        serializer = UserProfileSerializer(queryset, many=True)

        serializer.data[0].update({"dependants": dep_serializer.data})
        serializer.data[0].update({"initial_facility": Facilities.objects.get(mfl_code=serializer.data[0]['initial_facility']).name})
        serializer.data[0].update({"current_facility": Facilities.objects.get(mfl_code=serializer.data[0]['current_facility']).name})
        serializer.data[0].update({"current_treatment": RegimentSerializer(reg).data})
        return Response(data={"data": serializer.data}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def update_user(request):
    if request.method == 'PUT':
        u = User.objects.get(id=request.user.id)
        serializer = UserUpdateSerializer(u, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def update_dependant(request):
    if request.method == 'PUT':
        u = Dependants.objects.get(id=request.data['id'])
        serializer = DependantUpdateSerializer(u, data=request.data)
        if u.user != request.user:
            raise serializers.ValidationError("Dependant is not registered to user")
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_dependant(request):
    if request.method == "POST":
        try:
            queryset = Dependants.objects.get(id=request.data['id'])
        except Exception:
            raise serializers.ValidationError("Dependant Does Not Exist")
        if queryset.user != request.user:
            raise serializers.ValidationError("Dependant is not registered to user")
        serializer = DependantSerializer(queryset)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def elevate_dependant(request, dep_id):
    if request.method == 'POST':
        data_copy = request.data.copy()
        if Dependants.objects.get(id=dep_id).user != request.user:
            raise serializers.ValidationError("Dependant is not registered to user")
        elif EidResults.objects.filter(dependant=dep_id).order_by('-date_sent').first().result_content == 'Positive':
            d = Dependants.objects.get(id=dep_id)
            d.CCCNo = data_copy['CCCNo']
            d.save()
            a = Dependants.objects.filter(heiNumber=d.heiNumber)
            for i in a:
                i.CCCNo = data_copy['CCCNo']
                i.save()
            return Response({"success": True,
                             'data': "CCC number {} added".format(d.CCCNo)}, status=status.HTTP_202_ACCEPTED)
        else:
            raise serializers.ValidationError("Dependant is not registered to user")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    appoint = Appointments.objects.filter(user=request.user)
    vlr = VLResult.objects.filter(user=request.user)
    if appoint.count() == 0 and vlr.count() == 0:
        return Response({"success": False,
                         "Info": "No Appointments and Result for user"}, status=status.HTTP_200_OK)

    arr = []
    booked = 0
    for f in appoint:
        if datetime.strptime(str(date.today()), '%Y-%m-%d') > datetime.strptime(str(f.appntmnt_date), '%Y-%m-%d'):
            arr.append(f.app_status)
            if f.visit_type == 'ReScheduled':
                booked += 1
    arr.sort()
    b = dict((x, arr.count(x)) for x in set(arr))
    results = Appointments.objects.filter(user=request.user).exclude(app_status="Notified")
    kept = len(arr) - results.count()
    missed = results.count()
    b.update({'kept appointment': kept, 'missed appointment': missed, 'booked appointments': booked, 'total': len(arr)})
    arr = []
    for f in results:
        arr.append(f.app_type)
    arr.sort()
    a = dict((x, arr.count(x)) for x in set(arr))
    a = {k: v for k, v in sorted(a.items(), key=lambda x: x[1], reverse=True)}
    a.update({'total missed': missed})

    results = VLResult.objects.filter(user=request.user, owner='Personal').order_by("-date_sent")
    supr = []
    arr = []
    for f in results:
        arr.append(f.result_content)
    for r in results:
        if r.result_content == "< LDL " or int(r.result_content) < 1000:
            supr.append(1)
        else:
            supr.append(2)
    seq = [i for i in range(1, len(supr)) if supr[i] != supr[i - 1]]
    print(supr)
    print(seq)
    diff_sup = ""
    diff_unsup = ""
    current = "No Data"
    try:
        if supr[0] == 1:
            current = "Currently Suppressed"
            try:
                print(supr, seq, results)
                diff_sup = datediff(results[seq[0] - 1].date_sent, date.today())
            except:
                if len(supr) > 0:
                    diff_sup = datediff(results.last().date_sent, date.today())
                else:
                    diff_sup = "0 days"
            try:
                diff_unsup = datediff(results[seq[1] - 1].date_sent, results[seq[0] - 1].date_sent)
            except:
                if len(seq) == 1:
                    diff_unsup = datediff(results[seq[0]].date_sent, results[seq[0] - 1].date_sent)
                else:
                    diff_unsup = "0 days"

        elif supr[0] == 2:
            current = "Currently Unsuppressed"
            try:
                diff_sup = datediff(results[seq[1] - 1].date_sent, results[seq[0] - 1].date_sent)
            except IndexError:
                if len(seq) == 1:
                    diff_sup = datediff(results[seq[0]].date_sent, results[seq[0] - 1].date_sent)
                else:
                    diff_sup = "0 days"
            try:
                diff_unsup = datediff(results[seq[0] - 1].date_sent, date.today())
            except IndexError:
                if len(supr) > 0:
                    diff_unsup = datediff(results.last().date_sent, date.today())
                else:
                    diff_unsup = "0 days"

    except IndexError:
        diff_sup = "No data"
        diff_unsup = "No data"

    return Response({"success": True, "data": {'all apointments': b,
                                               'missed per type': a,
                                               'days suppressed': diff_sup,
                                               'days unsuppressed': diff_unsup,
                                               'current status': current}},
                    status=status.HTTP_200_OK)


def datediff(d1, d2):
    date1 = datetime.strptime(str(d1).split(" ")[0], '%Y-%m-%d')
    date2 = datetime.strptime(str(d2).split(" ")[0], '%Y-%m-%d')
    diff = relativedelta.relativedelta(date2, date1)
    return '{} years {} months {} days'.format(diff.years, diff.months, diff.days)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def regiment_history(request):
    if request.method == 'POST':
        data_copy = request.data.copy()
        data_copy.update({"user": request.user.id})
        queryset = Regiment.objects.filter(user=request.user.id).order_by('-date_started')
        c = check_ccc(request.user.CCCNo)
        if data_copy['is_same_art']:
            if c is False:
                raise serializers.ValidationError('ART DATE NOT FOUND')
            elif queryset.count() > 0:
                print(datetime.strptime(data_copy['date_started'], '%Y-%m-%d').date() > queryset.first().date_started)
                raise serializers.ValidationError('Date cannot be added because data already exists')
            else:
                data_copy.update({"date_started": datetime.strptime(str(c['art_date'].split('T')[0]), '%Y-%m-%d')})
        else:
            if datetime.strptime(data_copy['date_started'], '%Y-%m-%d').date() <= queryset.first().date_started:
                raise serializers.ValidationError('Date cannot be before that previous start date {}'.format(
                    datetime.strptime(data_copy['date_started'], '%Y-%m-%d')))

            # TODO add art date
        serializer = RegimentSerializer(data=data_copy)
        print(serializer.is_valid())
        try:
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'GET':
        queryset = Regiment.objects.filter(user=request.user.id).order_by('-date_started')
        queryset2 = Regiment.objects.filter(user=request.user.id).order_by('-date_started')[1:]
        if queryset2.count() == 0:
            if queryset.count() == 0:
                return Response({"success": False, "data": "No regiment data"}, status=status.HTTP_200_OK)
            else:
                serializer = RegimentSerializer(queryset[0])
                return Response({"success": True, "previous regiments": [], "current regiment": serializer.data}, status=status.HTTP_200_OK)
        else:
            serializer = RegimentSerializer(queryset2, many=True)
            serializer2 = RegimentSerializer(queryset.first())
            ser = serializer.data
            date_c = serializer2.data['date_started']
            for s in ser:
                s.update({'end_date': date_c})
                date_c = s['date_started']

            return Response({"success": True, "previous regiments": serializer.data, "current regiment": serializer2.data},
                            status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_facilities_all(request):
    queryset = Facilities.objects.all()
    serializer = FacilitySerializer(queryset, many=True)
    return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def approve_dep(request, dep_id):
    try:
        d = Dependants.objects.get(id=dep_id)
    except Exception:
        return Response({"success": False, "error": "Dependant does not exist"},
                        status=status.HTTP_401_UNAUTHORIZED)
    if d.user != request.user:
        return Response({"success": False, "error": "Dependant not registered to User"},
                        status=status.HTTP_401_UNAUTHORIZED)
    elif d.approved == "Approved":
        return Response({"success": False, "error": "Dependant already approved"},
                        status=status.HTTP_403_FORBIDDEN)
    else:
        all_dep = Dependants.objects.filter(id=dep_id).update(approved="Approved")
        print(all_dep)
        return Response({"success": True, "data": "Dependant approved {}".format(d.id)}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def web_dash(request):
    u = request.user
    print(request.user.CCCNo)
    if request.user.CCCNo == "1":
        appointments = Appointments.objects.all()
        reg = User.objects.annotate(text_len=Length('CCCNo')).filter(text_len=10)
        reg_chart = User.objects.annotate(text_len=Length('CCCNo')).filter(text_len=10).values('date_joined__date').annotate(count=Count('id')).values('date_joined__date', 'count').order_by('date_joined__date')
        reg_last = User.objects.annotate(text_len=Length('CCCNo')).filter(text_len=10).values('last_login__date').annotate(count1=Count('id')).values('last_login__date', 'count1', 'id').order_by('last_login__date')
        date = []
        llogin = []
        joined = []
        all = []
        for r in reg_chart:
            r['date'] = r.pop('date_joined__date')
        for r in reg_last:
            r['date'] = r.pop('last_login__date')
        # print(reg_chart, reg_last)
        to_be_deleted = []
        for r in reg_chart:
            # r.update({'count_last': 0})
            for a in reg_last:
                if r['date'] == a['date']:
                    r.update(a)
                    to_be_deleted.append(a['id'])
                    print(r)
        reg_last.exclude(id__in=to_be_deleted)
        for r in reg_chart:
            try:
                r['count1']
            except:
                r.update({'count1': 0})
            all.append(r)
        for r in reg_last:
            r.update({'count': 0})
            all.append(r)
        print(all)
        # all.sort(key=itemgetter('date'), reverse=True)
        for a in all:
            date.append(a['date'])
            joined.append(a['count'])
            llogin.append(a['count1'])
        context = {
            # 'user': u,
            'app_count': appointments.count(),
            'reg_count': reg.count(),
            'vl_count': VLResult.objects.all().count(),
            'fac_count': Facilities.objects.all().count(),
            'eid_count': EidResults.objects.all().count(),
            'chart': {
                'date': date,
                'joined': joined,
                'llogin': llogin
            }
        }
    else:
        return PermissionDenied()
    return Response(context)


@api_view(['POST'])
def web_login(request):
    return

# class UserLogoutAllView(views.APIView):
#     """
#     Use this endpoint to log out all sessions for a given user.
#     """
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, *args, **kwargs):
#         user = request.user
#         user.jwt_secret = uuid.uuid4()
#         user.save()
#         return Response(status=status.HTTP_200_OK)

# TODO do approval of emancipated dependants