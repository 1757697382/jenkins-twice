# coding: utf-8
import os
import jinja2
import jenkins
import base64
import pymysql
#import mysqldb_model
import time
import datetime
from functools import wraps
from flask import Flask,request,render_template,url_for,redirect,flash,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from jinja2 import Environment,FileSystemLoader




#初始化
app = Flask(__name__,template_folder='templates',instance_path="/opt/app-root/src/config_private/",instance_relative_config=True)
app.config.from_pyfile('config_private.py')
db_user = app.config["USER"]
db_pass = app.config["PASS"]
db_url =  app.config["URL"]
jenkins_url = app.config["JENKINS_URL"]
user_id = app.config["USER_ID"]
api_token = app.config["API_TOKEN"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://%s:%s@%s:3306/is_jenkins'%(db_user,db_pass,db_url)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'this is is fu'

db = SQLAlchemy(app)

############################################
# 数据库
############################################
# 定义ORM
class admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(50))


    def __repr__(self):
        return '<admin %r>' % self.username
############################################
# 辅助函数、装饰器
############################################

# 登录检验（用户名、密码验证）
def valid_login(username, password):
    user = admin.query.filter(and_(admin.name == username, admin.password == password)).first()
    if user:
        return True
    else:
        return False

# 登录
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('username'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('adminlogin', next=request.url))
    return wrapper



#首页
@app.route('/',methods=['POST','GET'])
def index():
    if request.method == 'POST':
        token = request.form.get('token')
        print(token)
        if token:
            db = pymysql.connect(db_url, db_user, db_pass, "is_jenkins")
            print("连接成功")
            # 使用 cursor() 方法创建一个游标对象 cursor
            cursor = db.cursor()
            sql = "select type from jenkins_info where token='%s'" %token
            try:
                cursor.execute(sql)
                results = cursor.fetchall()
                for row in results:
                    #print(type(row[0]))
                    type = int(row[0])
                    print(type)
                    if type == 1:
                        print(1)
                        return redirect(url_for('create_web',token=token))
                    else:
                        print(2)
                        return redirect(url_for('create',token=token))
                db.commit()
            except:
                error = "未找到token"
                print("未找到token-index")
                return render_template('/result/error.html', error=error)

             # 关闭数据库连接
            db.close()
        else:
            return render_template('index.html')
    return render_template('index.html')

#token获取
@app.route('/token/',methods=['POST','GET'])
def get_token():
    if request.method == 'POST':
            username = request.form.get('username')
            #连数据库
            db = pymysql.connect(db_url, db_user, db_pass, "is_jenkins")
            print("连接成功")
            # 使用 cursor() 方法创建一个游标对象 cursor
            cursor = db.cursor()
            sql = "select token,time from jenkins_info where name='%s'" %username
            try:
                # 执行sql语句
                token = []
                time = []
                cursor.execute(sql)
                results = cursor.fetchall()
                print(len(results))
                for row in results:
                    #time = datetime.datetime.strptime(row[1],'%Y-%m-%d %H:%M:%S')
                    dt = row[1].strftime('%Y-%m-%d %H:%M:%S')
                    dtime = (datetime.datetime.now()-row[1]).days
                    dstime = (datetime.datetime.now()-row[1]).seconds
                    print("相差天数：%s"%dtime)
                    print("相差秒数：%s"%dstime)
                    #print(type(dstime))
                    lefttime = str(datetime.timedelta(seconds=86400-dstime))
                    #lefttime = str(datetime.timedelta(seconds=dstime))
                    print(lefttime)
                    print(type(dtime))
                    if dtime<1:
                        time.append(lefttime)
                        token.append(row[0])
                    #token = row[0]
                if len(results)>0:
                    length = len(token)
                    print(length)
                    tetk = {}
                    for i in range(length):
                        tetk[time[i]] = token[i]
                    return render_template('/token/get_token.html',tetk=tetk)
                else:
                    print("没信息啊")
                    message = '请您仔细检查邮箱前缀是否正确，确定之后，请联系管理员绑定信息！'
                    print("1")
                    return render_template('/token/get_token.html',message=message)
                db.commit()
            except:
                error = "未找到token"
                print("mei未找到token")
                return render_template('/result/error.html', error=error)

            # 关闭数据库连接
            db.close()

    return render_template('/token/get_token.html')



#管理员登陆
@app.route('/admin/',methods=['POST','GET'])
def adminlogin():
    if request.method == 'POST':
        if valid_login(request.form['adminusername'], request.form['password']):
            print("登陆成功")
            session['username'] = request.form.get('adminusername')
            print("session查询成功")
            return redirect(url_for('jobadmin'))
        else:
            error = '错误的用户名或密码'
            return render_template('/result/error2.html',error=error)

    return render_template('/admin/index.html')
#绑定job信息
@app.route('/admin/jobadmin/',methods=['POST','GET'])
@login_required
def jobadmin():
    if request.method == 'POST':

        db = pymysql.connect(db_url, db_user, db_pass, "is_jenkins")
        print("连接成功")
         # 使用 cursor() 方法创建一个游标对象 cursor
        cursor = db.cursor()
        username = request.form.get('username')
        #生成token
        token = username + (base64.b32encode(os.urandom(20))).decode()
        job_name = request.form.get('job_name')
        job_name_list = job_name.split('-')
        type = 0
        if "fe" in job_name_list:
            type = 1
        # 连接jenkins
        server = jenkins.Jenkins(jenkins_url, username=user_id, password=api_token)
        if server.job_exists(job_name):
            error = "job已存在，请另外起一个名字"
            return render_template('/result/error1.html', error=error)
           # "job已存在，请另外起一个名字"
        else:
            sshserver = request.form.get('sshserver')
            desc = request.form.get('description')
            print(username,token,job_name, sshserver,desc)
        sql = "INSERT INTO `is_jenkins`.`jenkins_info` (`name`, `token`, `job_name`, `sshserver`, `desc`, `type`) VALUES ( '%s', '%s', '%s', '%s', '%s' ,'%d')"  %(username,token,job_name,sshserver,desc,type)
        try:
            # 执行sql语句
            cursor.execute(sql)
            print("执行成功")
            # 提交到数据库执行
            db.commit()
        except:
            db.rollback()
            print("失败回滚")
            error = "数据重复,请重新绑定"
            return render_template('/result/error1.html', error=error)
            #return "数据重复"
        # 关闭数据库连接
        db.close()
        return render_template('/result/result1.html', result="绑定成功")
    return render_template('/admin/jobadmin.html')



#创建后端job
@app.route('/create/baga/',methods=['POST','GET'])
def create():
        if request.method == 'POST':
            token = request.args.get('token')
            print(token)

            #连接数据库
            db = pymysql.connect(db_url, db_user, db_pass, "is_jenkins")
            print("连接成功")
            # 使用 cursor() 方法创建一个游标对象 cursor
            cursor = db.cursor()
            sql = "select * from jenkins_info where token='%s' " %token
            try:
                    # 执行sql语句
                    cursor.execute(sql)
                    print("执行成功")
                    results = cursor.fetchall()
                    print(results)
                    if len(results) > 0:
                        for row in results:
                            job_name = row[3]
                            sshserver = row[4]
                            desc = row[5]
                            time = row[6]
                            print(job_name, sshserver, desc,time)
                    else:
                        error = "错误，找不到数据"
                        return render_template('/result/error.html', error=error)
            except:
                    error = "错误，找不到数据"
                    return render_template('/result/error.html', error=error)
            # 关闭数据库连接
            db.close()
            dtime = (datetime.datetime.now() - time).days
            print("相差天数：%s" % dtime)
            ditime = int(dtime)
            if ditime>=1:
                message = "对不起，token已过期"
                return render_template('index.html',message=message)
            else:
                # 获取参数
                app_name = request.form.get('app_name')
                port = request.form.get('port')
                jar_name = request.form.get('jar_name')
                cmd1= request.form.get('cmd')
                list = cmd1.split(' ')
                cmd = "java -Xms256m -Xmx256m"
                xianzhi = "-Xms"
                print(list)
                for i in range(1, len(list)):
                    if xianzhi not in list[i]:
                        cmd = cmd + " " + list[i]
                    else:
                        cmd = cmd1
                        break;
                git_url = request.form.get('git_url')
                branch = request.form.get('branch')
            # 连接jenkins
            server = jenkins.Jenkins(jenkins_url, username=user_id, password=api_token)
            #初始化环境
            env = Environment(loader=FileSystemLoader('./'))
            tmp = env.get_template('api.xml')
            try:
               xml = tmp.render(desc=desc, app_name=app_name, port=port, jar_name=jar_name, cmd=cmd,git_url=git_url, branch=branch, sshserver=sshserver)
            except:
                error = "请先填入token再创建"
                return render_template('/result/error.html', error=error)
            #构建
            try:
                server.create_job(job_name, xml)
            except:
                error = "job已存在"
                return render_template('/result/error.html', error=error)
            if server.job_exists(job_name):
                result = "创建成功"
                result = jenkins_url+'job/'+job_name
                return render_template('/result/result.html',result=result)
            else:
                error_result = "构建失败"
                return render_template('/result/result.html',error_result=error_result)
        return render_template('/create/baga.html')

#创建前端job
@app.route('/create/create_web/',methods=['POST','GET'])
def create_web():
        if request.method == 'POST':

            token = request.args.get('token')
            print(token)

            #连接数据库
            db = pymysql.connect(db_url, db_user, db_pass, "is_jenkins")
            print("连接成功")
            # 使用 cursor() 方法创建一个游标对象 cursor
            cursor = db.cursor()
            sql = "select * from jenkins_info where token='%s' " %token
            try:
                    # 执行sql语句
                    cursor.execute(sql)
                    print("执行成功")
                    results = cursor.fetchall()
                    print(results)
                    if len(results) > 0:
                        for row in results:
                            job_name = row[3]
                            sshserver = row[4]
                            desc = row[5]
                            time = row[6]
                            print(job_name, sshserver, desc,time)
                    else:
                        error = "错误，找不到数据"
                        return render_template('/result/error.html', error=error)
            except:
                    error = "错误，找不到数据"
                    return render_template('/result/error.html', error=error)
            # 关闭数据库连接
            db.close()
            dtime = (datetime.datetime.now() - time).days
            print("相差天数：%s" % dtime)
            ditime = int(dtime)
            if ditime>=1:
                message = "对不起，token已过期"
                return render_template('index.html',message=message)
            else:
                # 获取参数
                git_url = request.form.get('git_url')
                contextpath = request.form.get('contextpath')
            # 连接jenkins
            server = jenkins.Jenkins(jenkins_url, username=user_id, password=api_token)
            #初始化环境
            env = Environment(loader=FileSystemLoader('./'))
            tmp = env.get_template('web.xml')
            try:
                xml = tmp.render(desc=desc,git_url=git_url,sshserver=sshserver,contextpath=contextpath)
            except:
                error = "请先填入token再创建"
                return render_template('/result/error.html', error=error)
            #构建
            try:
                server.create_job(job_name, xml)
            except:
                error = "job已存在"
                return render_template('/result/error.html', error=error)
            if server.job_exists(job_name):
                result = "创建成功"
                result = jenkins_url+'job/'+job_name
                return render_template('/result/result.html',result=result)
            else:
                error_result = "构建失败"
                return render_template('/result/result.html',error_result=error_result)
        return render_template('/create/create_web.html')







if __name__ == "__main__":
    app.run(host='0.0.0.0')
