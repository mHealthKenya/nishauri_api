FROM python:3.10
# setup environment variable
#ENV DockerHOME=/home/project

# set work directory RUN mkdir -p $DockerHOME
RUN mkdir /project

# where your code lives  WORKDIR $DockerHOME
WORKDIR /project
ADD requirements.txt /project

RUN pip install -r requirements.txt

RUN virtualenv --no-site-packages env
RUN source env/bin/activate

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD . /project/

ADD entrypoint.sh /project
RUN chmod +x *.sh


# port where the Django app runs
EXPOSE 8000
# start server
#CMD python manage.py makemigrations
CMD python manage.py migrate
CMD python manage.py runserver 0.0.0.0:8000

