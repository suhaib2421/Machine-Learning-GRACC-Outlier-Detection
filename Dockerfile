FROM python:3-buster

ADD . /HCC
WORKDIR /HCC

RUN pip install -U -q elasticsearch elasticsearch_dsl numpy scikit-learn
RUN python -m pip install matplotlib
RUN python -m pip install pandas
RUN python -m pip install config

ENTRYPOINT ["python", "/HCC/sendMail.py"]
