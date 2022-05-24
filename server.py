from sanic import Sanic,response
import hmac,random,sys,math,datetime,time,json,urllib
from sanic_ipware import get_client_ip
from dbhelper import db,ipDB,statisticDB,powDB,sessionDB
import toolutils
import pow
                       
app = Sanic(__name__)
app.debug = False
app.access_log=False
app.config.PROXIES_COUNT=1
from sanic_useragent import SanicUserAgent
SanicUserAgent.init_app(app)

    
def iphandler(request):
    UA=request['user_agent'].to_dict()
    IP=get_client_ip(request)[0]
    func_name=sys._getframe().f_back.f_code.co_name
    ipDBpipe=ipDB.pipeline()
    ipDBpipe.hincrby(IP,func_name)
    ipDBpipe.hset(IP,"last_request",toolutils.timestring())
    ipDBpipe.hset(IP,"user_agent",UA["string"])
    #ipDBpipe.hincrby(IP,'total') 
    ipDBpipe.execute()
    ipDB.hset(IP,"ip_index",ipDB.hget(IP,func_name))
    statisticDBpipe=statisticDB.pipeline()
    statisticDBpipe.incr('total')
    statisticDBpipe.incr(func_name)
    statisticDBpipe.execute()
    #print(ipDB.hgetall(IP))
    #print(ipDB.get(func_name))
    #print(ipDB.get('total'))
    return {"IP":IP,"UA":UA,"func_name":func_name}
    
@app.middleware('request')
async def check_session(request):
    session = request.cookies.get('session')
    print(session)
    if session and sessionDB.exists(session):
        request["session"]=session
    else:
        request["session"]=None
    
@app.middleware('response')
async def add_session(request, response):
    if not "detail" in request:
        return
    print(request["detail"])
    sessionDBpipe=sessionDB.pipeline()
    if not request["session"]:
        index=statisticDB.get("total")
        session=toolutils.encrypt(index)
        request["session"]=session
        response.cookies['session'] = session
        sessionDBpipe.hset(session,"ip",request["detail"]["IP"])
        sessionDBpipe.hset(session,"user_agent",request["detail"]["UA"]["string"])
        sessionDBpipe.hset(session,"generate_timestamp",toolutils.timestring())
        append_session_to_ipDB(request["detail"]["IP"],session)
    sessionDBpipe.hincrby(request["session"],request["detail"]["func_name"])
    sessionDBpipe.hset(request["session"],"last_request",toolutils.timestring())  
    sessionDBpipe.execute()
    #response.headers["Access-Control-Allow-Origin"] = request.headers["origin"] if "origin" in request.headers else '*'
    #response.headers["Access-Control-Allow-Credentials"] ="true"
    
def append_session_to_ipDB(ip,session):
    t=ipDB.hget(ip,"session")
    result=json.loads(t) if t else []
    result.append(session)
    ipDB.hset(ip,"session",json.dumps(result))
        
    
@app.route('/generate')
def generateAPI(request):
    request["detail"]=iphandler(request)
    index=statisticDB.get(sys._getframe().f_code.co_name)
    nonce=urllib.parse.quote_plus(hmac.new(b"gM*TOs&YpMCRiDUG",bytes(index,encoding='utf8'), digestmod="MD5").hexdigest())
    evil=2**16 #random.randint(1,100)
    parsed=pow.parse(evil)
    powDBpipe=powDB.pipeline()
    powDBpipe.hset(nonce,"total_index",index)
    powDBpipe.hset(nonce,"ip",request["detail"]["IP"])
    powDBpipe.hset(nonce,"user_agent",request["detail"]["UA"]["string"])
    powDBpipe.hset(nonce,"ip_index",ipDB.hget(request["detail"]["IP"],sys._getframe().f_code.co_name))
    powDBpipe.hset(nonce,"puzzle",json.dumps(parsed))
    powDBpipe.hset(nonce,"generate_timestamp",toolutils.timestring())
    powDBpipe.hset(nonce,"verified",0)
    powDBpipe.hset(nonce,"session",request["session"])
    powDBpipe.execute()
    sessionDB.hset(request["session"],"nonce",nonce)
    return response.json({"success":1,"description":"","nonce":nonce,"puzzle":parsed})
    
@app.route('/verify')
def verifyAPI(request):
    request["detail"]=iphandler(request)
    result=request.args.get('result')
    nonce=request.args.get('nonce')
    temp=powDB.hgetall(nonce)
    if pow.verify(nonce+result,json.loads(temp["puzzle"])):
        powDBpipe=powDB.pipeline()
        powDBpipe.hset(nonce,"verified",1)
        powDBpipe.hset(nonce,"verified_timestamp",toolutils.timestring())
        powDBpipe.execute()
        sessionDB.hincrby(request["session"],"success_count")
        ipDB.hincrby(request["detail"]["IP"],"success_count")
        return response.json({"success":1,"description":"验证成功"})
    return response.json({"success":0,"description":""})
    
@app.route('/check')
def resultAPI(request):
    
    def check_nonce(nonce):
        if not powDB.exists(nonce):
            return {"success":0,"description":"nonce不存在"}
        if session and session!=powDB.hget(nonce,"session"):
            return {"success":0,"description":"发起人不一致"}
        if not powDB.hget(nonce,"verified"):   
            return {"success":0,"description":"验证未完成"}
        return {"success":1}
            
    request["detail"]=iphandler(request)
    type=request.args.get("type")
    payload=request.args.get("payload")
    session=request.args.get("session")
    if type == "nonce":
        return response.json(check_nonce(payload))
    elif type == "session":
        print(session)
        if not sessionDB.exists(session):
            return response.json({"success":0,"description":"session不存在"})
        result=sessionDB.hgetall(session)
        return response.json({**check_nonce(result["nonce"]),**result})
    elif type == "ip":    
        if not ipDB.exists(payload):
            return response.json({"success":0,"description":"ip不存在"})
        result=ipDB.hgetall(payload)    
        return  response.json(result)      

from captcha.image import ImageCaptcha
@app.route('/img')
def image(request):
    request["detail"]=iphandler(request)
    image = ImageCaptcha()
    string = toolutils.ranstr(4)
    sessionDB.hset(request["session"],"image_captcha_string",string)
    data = image.generate(string)
    body = data.getvalue()
    content_type = 'image/png'
    return response.raw(body=body,content_type=content_type)
@app.route('/img/verify')
def imageverify(request):
    request["detail"]=iphandler(request)
    result=request.args.get("result")
    if not result:
        return response.json({"success":0,"description":"验证码不能为空"})   
    if result.lower() != sessionDB.hget(request["session"],"image_captcha_string").lower():
        return response.json({"success":0,"description":"验证码错误"})   
    return response.json({"success":1,"description":"验证成功"})
from captcha.audio import AudioCaptcha
@app.route('/audio')
def audio(request):
    request["detail"]=iphandler(request)
    audio = AudioCaptcha(voicedir="/www/wwwroot/powCAPTCHA/voices")
    string = toolutils.ranstr(4)
    print(string)
    sessionDB.hset(request["session"],"audio_captcha_string",string)
    data = audio.generate(string)
    content_type = 'audio/wav'
    return response.raw(body=data,content_type=content_type)
@app.route('/audio/verify')
def audioverify(request):
    request["detail"]=iphandler(request)
    result=request.args.get("result")
    if not result:
        return response.json({"success":0,"description":"验证码不能为空"})   
    if result.lower() != sessionDB.hget(request["session"],"audio_captcha_string").lower():
        return response.json({"success":0,"description":"验证码错误"})   
    return response.json({"success":1,"description":"验证成功"})    
@app.route('/getsession')
def getsession(request):
    request["detail"]=iphandler(request)
    return response.text(request["session"])    
@app.route('/statistics')
def statistics(request):
     request["detail"]=iphandler(request)
     type=request.args.get("type")
     elapsed=request.args.get("elapsed")
     success=request.args.get("success")
     print(type,elapsed,success)
     db.insertsqlone(tablename="statistics", type=type, elapsed=elapsed, success=success,ua=request["detail"]["UA"]["string"],ip=request["detail"]["IP"],timestamp=toolutils.timestring())
     return response.json({"success":1})  
@app.route('/')
def homePage(request):
    request["detail"]=iphandler(request)
    return response.file("index.html")

if __name__ == '__main__':
   app.run(host="0.0.0.0",port=1080)
