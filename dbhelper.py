#coding=utf-8



######################################### 以下为redis内存数据库############################

import redis # 由于redis输出数据类型是bytes，所以连接配置提供decode_responses选项，可以选择直接输出str类型数据 
redisdic={30:"ipDB",31:"statisticDB",32:"powDB",33:"sessionDB"}

redis.ConnectionPool(host='localhost', port=6379, password='******',decode_responses=True)

for key,value in redisdic.items():
   exec(value+"""= redis.Redis(connection_pool=redis.ConnectionPool(host='localhost', port=6379, password='******',decode_responses=True,db="""+str(key)+"""))""")
print("内存数据库启动完成")





######################################### 以下为MYSQL数据库（已完成）############################
import pymysql
class DiyMysql(object):

    def __init__(self, host, port, user, passwd, db, charset):
        print("mysql数据库启动！")
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.db = db
        self.charset = charset
        try:
            self.condb = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                         passwd=self.passwd, db=self.db, charset=self.charset)         
            self.condb.autocommit(True)
        except Exception as abnormal:
            print("数据库连接错误，错误内容%s " % abnormal)
        # 创建一个游标对象
        self.cursor = self.condb.cursor()

    def maketable(self, tablename, **field):

        basesql = ""  # 定义basesql
        # 判断表名为tablename表名是否存在，如果是 直接删除
        self.cursor.execute("DROP TABLE IF EXISTS %s" % tablename)

        # 将field，拼接basesql
        for key in field:
            basesql = basesql + "%s varchar(255) DEFAULT NULL COMMENT '%s'," % (key, field.get(key))

        makesql = """
        CREATE TABLE %s (
  id int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  %s
  PRIMARY KEY (`id`)
)
        """ % (tablename, basesql)
        # 执行建表SQL
        self.condb.ping(reconnect=True)
        self.cursor.execute(makesql)
        print("表:'%s' 创建成功" % tablename)

    def insertsqlone(self, tablename, **field):

        i = 0
        liststr = ""  # 字段的集合
        listvalues = []  # values字段对应值的集合
        for key in field:
            liststr = liststr + "%s," % key
            listvalues.append(field[key])
            i = i + 1
        listfield = "(" + liststr[0:len(liststr) - 1] + ")"  # 最终的字段集合
        values = tuple(listvalues)  # 最终的字段值集合

        # sql语句
        insertsql = "INSERT INTO %s%s VALUES %s" % (tablename, listfield, values)
        try:
            self.condb.ping(reconnect=True)
            self.cursor.execute(insertsql)  # 执行SQL
            self.condb.commit()  # 提交到数据库执行
        except Exception as abnormal:
            self.condb.rollback()  # 发生错误的时候 回滚
            print("执行失败 insert语句:'%s'，失败信息为 %s" % (insertsql, abnormal))
        # 判断是否执行成功
        if self.cursor.rowcount == 1:
            print("执行成功 insert语句:'%s'" % insertsql)

    def querysql(self, sqlquery):
        try:
            self.condb.ping(reconnect=True)
            self.cursor.execute(sqlquery)  # 影响的行数
        except Exception as abnormal:
            print("SQL有误，错误内容 %s" % abnormal)
            self.condb = pymysql.connect("localhost",3306, "root","wfkycEzzxjl1", "main", "utf8")
            self.cursor = self.condb.cursor()

        if self.cursor.rowcount == 0:  # 0 则代表没有查询结果
            return "没有查询到结果"
        elif self.cursor.rowcount == 1:  # 影响行数 为1 fetchone
            #print(dict(zip([x[0] for x in  self.cursor.description],[x for x in  self.cursor.fetchone()])))
            #return list(self.cursor.fetchone())
            return dict(zip([x[0] for x in  self.cursor.description],[(x if x is not None else "null") for x in  self.cursor.fetchone()]))
        else:  # 多行情况下 使用fetchall
            print(  list(map(dict(zip([x[0] for x in self.cursor.description],[x for x in new])),self.cursor.fetchall())) )
            return list(self.cursor.fetchall())

    def update(self, updatesql):
        try:
            self.condb.ping(reconnect=True)
            self.cursor.execute(updatesql)
            self.condb.commit()
        except Exception as abnormal:
            self.condb.rollback()
            print("执行失败!update语句:'%s', 失败内容为 %s" % (updatesql, abnormal))
            exit()
        # 判断是否更新成功
        if self.cursor.rowcount == 1:
            print("执行成功!update语句:'%s'" % updatesql)
        else:
            print("执行成功!update语句:'%s'，warning:更新后的值与跟新之前的值相等，或者查询不到对应的结果" % updatesql)

    def deleteone(self, deletesql):
        try:
            self.condb.ping(reconnect=True)
            self.cursor.execute(deletesql)
            self.condb.commit()
        except Exception as abnormal:
            self.condb.rollback()
            print("执行失败!delete语句:'%s', 失败内容为 %s" % (deletesql, abnormal))
            exit()
        # 判断是否更新成功
        if self.cursor.rowcount == 1:
            print("执行成功!delete语句:'%s'" % deletesql)

    # 析构函数
    def __del__(self):
        self.cursor.close()
        self.condb.close()
        print("mysql con完成析构")


db = DiyMysql(host="localhost", port=3306, user="root",passwd="wfkycEzzxjl1", db="powCAPTCHA", charset="utf8")

##
##  # 1.新建一个名称为的表，字段为name,age,address,其中的value为字段说明
##    diycon.maketable(tablename="tb_xiejiangpeng", name="姓名", age="年龄", address="家庭住址")
##
##    # 2.在tb_xiejiangpeng表中 插入一条数据
##    diycon.insertsqlone(tablename="tb_xiejiangpeng", name="谢江鹏", age="22", address="湖南长沙")
##
##    # 3.根据name=谢江鹏 查询刚才插入的数据
##    queryresult = diycon.querysql("select * from tb_xiejiangpeng where name='谢江鹏'")
##    print("查询到的结果为:", queryresult)
##
##    # 4.将id=1的那条数据 名称修改成"彭敏"
##    diycon.update("update tb_xiejiangpeng set name='彭敏' where id ='1'")
##
##    # 5.删除name='彭敏'的那条数据
##    diycon.delete("delete from tb_xiejiangpeng where name='彭敏'")
##--------------------- 
##作者：Tester_xjp 
##来源：CSDN 
##原文：https://blog.csdn.net/tester_xjp/article/details/83514975 
##版权声明：本文为博主原创文章，转载请附上博文链接！
