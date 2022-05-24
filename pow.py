import hashlib,random,math
def isprime(n):
    if n < 2: return False
    for i in range(2,int(math.sqrt(n))+1):
        if n % i == 0:
            return False
    return True

def removeprime(n):
    while True:
        n-=1
        if not isprime(n):
          return n 
          
def parse(val,t=None,strlen=64,count=0):
    assert 0<val<=16**strlen
    t = t if t else []   
    if count==strlen:
        return t
    if val==1:
        t.append(val)
        return parse(val,t,strlen,count+1)
    for i in range(16 if val>16 else val ,1,-1):
        if val%i==0:
            t.append(i)
            #print(i,val)
            return parse(int(val/i),t,strlen,count+1)
    return parse(removeprime(val),t,strlen,count)

def verify(s,t):
    s=hashlib.sha256(bytes(s,encoding='utf-8')).hexdigest()
    for i in range(len(s)):
        #print(int(s[i],16),t[i]-1)
        if int(s[i],16)>round(16/t[i])-1:
            return False
    return True