FROM blenderproc/blenderproc:v2

COPY . /usr/src/app/

RUN mkdir /data/vol2

WORKDIR /usr/src/app

COPY CocoWriterUtility.py /home/blenderproc/.local/lib/python3.8/site-packages/blenderproc/python/writer/CocoWriterUtility.py 

CMD ["blenderproc", "run", "main.py"]
