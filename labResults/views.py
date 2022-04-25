import datetime
from datetime import datetime

import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from authApp.models import *
from .serializer import *


@api_view(['GET'])
def saveLabs(request):
    users = User.objects.all()
    for user in users:
        c = check_lab(user.CCCNo)
        if c != {'message': 'No results for the given CCC Number were found'}:
            saveSyncVl(c, user, 'Personal')
    return


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_vload(request):
    if request.method == 'GET':
        r = VLResult.objects.filter(user=request.user, result_type='1', owner='Personal').order_by('-date_sent')
        if r.exists():
            serializer = VLSerializer(r, many=True)
            dat = serializer.data
            return Response(data={"data":dat}, status=status.HTTP_200_OK)

        dat = {'message': 'No results for the given CCC Number were found'}
        return Response(data=dat, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_dep_vload(request):
    if request.method == 'GET':
        li = []
        d = Dependants.objects.filter(user=request.user)
        for i in d:
            if i.CCCNo:
                res = check_lab(i.CCCNo)
                if res != {'message': 'No results for the given CCC Number were found'}:
                    save_vl(res, request, 'Dependant')

                r = VLResult.objects.filter(user=request.user, result_type='1',
                                            owner='Dependant').order_by('-date_sent')
                dep_ser = VLSerializer(r, many=True)

                for q in dep_ser.data:
                    q.update({'name': Dependants.objects.get(CCCNo=q['CCCNo']).first_name + ' ' + Dependants.objects.get(CCCNo=q['CCCNo']).surname})
                    li.append(q)

        else:
            li = {'message': 'No results for the given CCC Number were found'}

        return Response(data={"data": li}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_eid(request):
    if request.method == 'GET':
        ret = []
        d = Dependants.objects.filter(user=request.user, approved="Approved")
        for a in d:
            c = check_lab(a.heiNumber)
            if c == {'message': 'No results for the given CCC Number were found'}:
                c.update({"hei": a.heiNumber})
                # ret.append(c)
                continue
            for it in range(len(c["results"])):
                r = EidResults.objects.filter(r_id=c["results"][it]["id"])
                if r.count() == 0:
                    data = EidResults()
                    data.dependant = a
                    data.r_id = c["results"][it]["id"]
                    data.result_type = c["results"][it]["result_type"]
                    data.result_content = c["results"][it]["result_content"]
                    data.lab_name = c["results"][it]["lab_name"]
                    try:
                        data.date_sent = datetime.strptime(c["results"][it]["created_at"].split(" ")[0], '%Y-%m-%d')
                    except AttributeError:
                        data.date_sent = None

                    try:
                        data.date_collected = datetime.strptime(c["results"][it]["date_collected"].split(" ")[0], '%Y-%m-%d')
                    except Exception:
                        data.date_collected = None

                    data.save()
            r = EidResults.objects.filter(dependant=a, result_type="2").order_by('-date_sent')
            serializer = EidSerializer(r, many=True)
            for i in range(len(serializer.data)):
                serializer.data[i].update({"dependant": a.first_name + " " + a.surname})
            for v in serializer.data:
                ret.append(v)

        r = EidResults.objects.filter(dependant__in=d, result_type="2").order_by('-date_sent')
        print(r)
        serializer = EidSerializer(r, many=True)
        for i in range(len(serializer.data)):
            serializer.data[i].update({"dependant": Dependants.objects.get(id=serializer.data[i]["dependant"]).first_name + " " + Dependants.objects.get(id=serializer.data[i]["dependant"]).surname})
        return Response(data={"data": serializer.data}, status=status.HTTP_200_OK)


def check_lab(value):
    try:
        user = {
            "ccc_number": value
        }

        url = "https://mlab.kenyahmis.co.ke/api/ushauri/get/results"
        headers = {
            'content-type': "application/json",
            'Accept': 'application/json'
        }
        response = requests.post(url, data=user, json=headers, verify=False)
        print(response.json())
        return response.json()
    except ConnectionError as e:
        print(e)


def save_vl(c, a, o):
    for it in range(len(c["results"])):
        r = VLResult.objects.filter(r_id=c["results"][it]["id"])
        if r.count() == 0:
            data = VLResult()
            data.user = a.user
            data.r_id = c["results"][it]["id"]
            data.result_type = c["results"][it]["result_type"]
            data.date_collected = c["results"][it]["date_collected"]
            data.lab_name = c["results"][it]["lab_name"]
            data.owner = o
            if o == 'Dependant':
                data.CCCNo = c["results"][it]['client_id']
            try:
                data.result_content = int(c["results"][it]["result_content"])
            except ValueError:
                data.result_content = c["results"][it]["result_content"][:-9]
            try:
                data.date_sent = datetime.strptime(c["results"][it]["created_at"].split(" ")[0], '%Y-%m-%d')
            except AttributeError:
                data.date_sent = None
            data.save()


def saveSyncVl(result, user, o):
    for it in range(len(result["results"])):
        r = VLResult.objects.filter(r_id=result["results"][it]["id"])
        if r.count() == 0:
            data = VLResult()
            data.user = user
            data.r_id = result["results"][it]["id"]
            data.result_type = result["results"][it]["result_type"]
            data.date_collected = result["results"][it]["date_collected"]
            data.lab_name = result["results"][it]["lab_name"]
            data.owner = o
            if o == 'Dependant':
                data.CCCNo = result["results"][it]['client_id']
            try:
                data.result_content = int(result["results"][it]["result_content"])
            except ValueError:
                data.result_content = result["results"][it]["result_content"][:-9]
            try:
                data.date_sent = datetime.strptime(result["results"][it]["created_at"].split(" ")[0], '%Y-%m-%d')
            except AttributeError:
                data.date_sent = None
            data.save()
