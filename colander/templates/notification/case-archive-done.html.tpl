<!DOCTYPE html>
<html>
  <head lang="en">
    <meta charset="UTF-8">
    <title>{{subject}}</title>
  </head>
  <body style="font-family: sans-serif;">
    <p>Dear user <strong>{{ user.username }}</strong>,</p>
    <p>
    A new archive is available and ready to be downloaded from your Colander instance,<br/>
    at the following address: <a style="color: #7122da;" href="{{url}}">{{url}}</a>.
    </p>
    <p>
    Regards,<br/>
    <i>The Colander Team</i>
    </p>
  </body>
</html>
