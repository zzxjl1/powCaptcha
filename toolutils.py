import random,datetime,time
import jinja2 
env = jinja2.Environment(loader=jinja2.FileSystemLoader('/'),
                         autoescape=jinja2.select_autoescape(['html']))
def render_template(tpl, **kwargs):
    template = env.get_template(tpl)
    return response.html(template.render(kwargs))  
    
def timestring():
    return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')[:-3] #去掉为纳秒精度
    
def ranstr(num=32):
    H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    salt = ''
    for i in range(num):
        salt += random.choice(H)
    return salt

from Crypto.Cipher import AES
import base64,urllib              
aes_key = "@t14RJgaDv7O!y*2" #空格误删，保证16位

"""
AES加密解密工具类
@author jzx
@date   2018/10/24
此工具类加密解密结果与 http://tool.chacuo.net/cryptaes 结果一致
数据块128位
key 为16位
iv 为16位，且与key相等
字符集utf-8
输出为base64
AES加密模式 为cbc
填充 pkcs7padding
"""
def pkcs7padding(text):
    text=str(text)
    """
    明文使用PKCS7填充
    最终调用AES加密方法时，传入的是一个byte数组，要求是16的整数倍，因此需要对明文进行处理
    :param text: 待加密内容(明文)
    :return:
    """
    bs = AES.block_size  # 16
    length = len(text)
    bytes_length = len(bytes(text, encoding='utf-8'))
    # tips：utf-8编码时，英文占1个byte，而中文占3个byte
    padding_size = length if(bytes_length == length) else bytes_length
    padding = bs - padding_size % bs
    # tips：chr(padding)看与其它语言的约定，有的会使用'\0'
    padding_text = chr(padding) * padding
    return text + padding_text


def pkcs7unpadding(text):
    """
    处理使用PKCS7填充过的数据
    :param text: 解密后的字符串
    :return:
    """
    length = len(text)
    unpadding = ord(text[length-1])
    return text[0:length-unpadding]


def encrypt(content):
    """
    AES加密
    key,iv使用同一个
    模式cbc
    填充pkcs7
    :param key: 密钥
    :param content: 加密内容
    :return:
    """
    key_bytes = bytes(aes_key, encoding='utf-8')
    iv = key_bytes
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    # 处理明文
    content_padding = pkcs7padding(content)
    # 加密
    encrypt_bytes = cipher.encrypt(bytes(content_padding, encoding='utf-8'))
    # 重新编码
    result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')
    return urllib.parse.quote_plus(result)


def decrypt(content):
    """
    AES解密
     key,iv使用同一个
    模式cbc
    去填充pkcs7
    :param key:
    :param content:
    :return:
    """
    content=urllib.parse.unquote(content)
    key_bytes = bytes(aes_key, encoding='utf-8')
    iv = key_bytes
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    # base64解码
    encrypt_bytes = base64.b64decode(content)
    # 解密
    decrypt_bytes = cipher.decrypt(encrypt_bytes)
    # 重新编码
    result = str(decrypt_bytes, encoding='utf-8')
    # 去除填充内容
    result = pkcs7unpadding(result)
    return result

print('aes_key:' + aes_key)
print(decrypt(encrypt("encrypt module test 加密模块测试123！  工作正常")))    