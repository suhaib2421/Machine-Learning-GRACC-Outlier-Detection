FROM gsantomaggio/sklearn

ADD . /HCC
WORKDIR /HCC

RUN pip install -U -q elasticsearch elasticsearch_dsl numpy scipy sklearn
RUN python -m pip install matplotlib
RUN python -m pip install pandas
RUN python -m pip install config

ENTRYPOINT ["python", "/HCC/sendMail.py"]
