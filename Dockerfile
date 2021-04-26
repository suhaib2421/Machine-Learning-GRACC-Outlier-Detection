FROM python:3-buster

RUN pip install -U -q elasticsearch elasticsearch_dsl numpy scikit-learn
RUN python -m pip install matplotlib
RUN python -m pip install pandas
RUN python -m pip install config
RUN python -m pip install tabulate

ADD . /HCC
WORKDIR /HCC

ENTRYPOINT ["python", "/HCC/sendMail.py"]
