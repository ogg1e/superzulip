# superzulip
A python script to send supervisord events to zulip

You need to install the zulip api from here:
https://github.com/zulip/zulip/tree/master/api

You also need to install:
```
python-six libffi libffi-devel openssl-devel 
```

```
pip install requests==2.5.3
pip install certifi
```

It hasn't been tested with self-signed certificates and requires an SSL cert since zulip itself does as well.  It also has only been tested against a private zulip server.

Add this to you supervisor setup:

```
[eventlistener:superzulip]
command=python /opt/zulip/superzulip.py --key="zulip-api-key" --stream="Supervisor" --user="supervisor-bot@mycompany.com" --apiPath="/api/v1/messages" --zhost="https://zulip.mycompany.com" --subject="MyServer" --cert="/etc/ssl/certs/ca-bundle.crt"
events=PROCESS_STATE,TICK_60
```

