
from flask import Flask, render_template, request, jsonify, make_response
from flask_jwt_extended import *
from hashlib import *
import datetime
import chachaconfig

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False #한글 깨짐 현상 해결코드
app.config['JWT_SECRET_KEY'] = chachaconfig.jwt_key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=5)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=10)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SESSION_COOKIE_SECURE'] = True

jwt = JWTManager(app)

# DB 관련
from pymongo import MongoClient


# 서버 db 사용시 로컬 db 주석 처리, 로컬 db 사용시 서버 db 주석 처리
# **********************************************************

# client = MongoClient('localhost', 27017)
client = MongoClient('mongodb://test:test@54.180.2.121', 27017)

db = client.dbchacha

# **********************************************************


# 차 정보 입력하기(POST) API

@app.route('/save', methods=['POST'])
def save_tea():
    print(request.is_json)
    tea_receive = request.get_json()
    name_receive = tea_receive['name_give']                   # 차 이름입니다
    #eng_name_receive = tea_receive['eng_name_give']          # (영문)차 이름입니다 - 사용 않아서 주석처리
    type_receive = tea_receive['type_give']                   # 대분류1 종류
    eng_type_receive = tea_receive['eng_type_give']           # 대분류1 (영문)종류 - 종류 선택시 자동 입력
    benefit_receive = tea_receive['benefit_give']             # 대분류2 효능
    caffeineOX_receive = tea_receive['caffeineOX_give']       # 대분류3 카페인 "함유여부" Boolean 없으면 False 있으면 True
    caffeine_receive = tea_receive['caffeine_give']           # 상세1 카페인 "함량"
    benefitdetail_receive = tea_receive['benefitdetail_give'] # 상세2 상세효능
    desc_receive = tea_receive['desc_give']                   # 상세2 상세설명
    caution_receive = tea_receive['caution_give']             # 상세3 주의사항
    img_receive = tea_receive['img_give']                     # 상세4 이미지 주소

    doc = {
        'name': name_receive,
        #'eng_name': eng_name_receive, # 영문명 입력 받지 않음에 의해 주석처리
        'type': type_receive,
        'benefit': benefit_receive,
        'caffeineOX': caffeineOX_receive,
        'caffeine': caffeine_receive,
        'benefitdetail': benefitdetail_receive,
        'desc': desc_receive,
        'caution': caution_receive,
        'img': img_receive,
    }

    db.tealist.insert_one(doc)

    return jsonify({'msg': '차 등록이 완료되었습니다!'})

@app.route('/')
def home():
    return render_template('save_tea.html')

# 티 정보 GET 하기 -- 영은
# ***************************************************************************************************
@app.route('/tea/list', methods=['GET'])
def getTea():
    tea_list = list(db.tealist.find({}, {'_id': False}).sort('name'))
    return jsonify({'all_teas':tea_list})

@app.route('/tea')
def teaList():
    return render_template('get_tea.html')
# ***************************************************************************************************

# like (seung)
# ***************************************************************************************************
@app.route('/tea/like', methods=['POST'])
def likeTea():
    name_receive = request.form['name_give']
    target_tea = db.tealist.find_one({'name': name_receive})
    current_like = target_tea['like']

    new_like = current_like + 1

    db.tealist.update_one({'name': name_receive}, {'$set': {'like': new_like}})
    return jsonify({'msg': 'like +1'})
# ***************************************************************************************************

# scrap (seung)
# ***************************************************************************************************
@app.route('/tea/scrap', methods=['POST'])
def scrapTea():
    name_receive = request.form['name_give']
    scrap_list = db.tealist.find_one({'name': name_receive})
    check_scrap = db.scraps.find_one({'name': name_receive})

    if check_scrap is not None:
        return jsonify({'alreadyScrap': '이미 찜 하셨습니다.'})
    else:
        db.scraps.insert_one(scrap_list)
        return jsonify({'successScrap': '찜 완료 되었습니다.'})

@app.route('/tea/scrapList', methods=['GET'])
def showScrapTea():
    scrap_list = list(db.scraps.find({}, {'_id': False}).sort("name"))
    return jsonify({'scrapTeas': scrap_list})

@app.route('/api/deleteScrap', methods=['POST'])
def delete_scrap():
    name_receive = request.form['name_give']
    db.scraps.delete_one({'name': name_receive})
    return jsonify({'msg': '삭제 완료'})

@app.route('/tea/scrapPage')
def scrapPage():
    return render_template('tea_scrap.html')

# ***************************************************************************************************

@app.route('/sign')
def signup1_page():
    return render_template('login.html')

#***************************************************************************************************
# mu-jun's function code


@app.route('/sign/checkID', methods=['POST'])

def checkID():

    id_receive = request.get_json().upper()
    result = db.users.find_one({'id': id_receive})

    if result is not None:
        return jsonify({'fail': '사용할 수 없는 ID입니다.'})
    else:
        return jsonify({'success': '사용 가능한 ID입니다.'})
    
@app.route('/sign/checkNickname', methods=['POST'])
def checkNickname():
    
    nickname_receive = request.get_json().upper()
    
    result = db.users.find_one({'id': nickname_receive})
    
    if result is not None:
        return jsonify({'fail': '사용할 수 없는 별명입니다.'})
    else:
        return jsonify({'success': '사용 가능한 별명입니다.'})

# 반복 솔팅?
def hash_pass(password, id):

    personal_key = id[:8].encode('utf-8')
    password = password+chachaconfig.salt_key

    for i in range(chachaconfig.iteration_num):
        password = password.encode('utf-8')
        password = blake2s(password,person=personal_key).hexdigest()

    return password

@app.route('/sign/signup_test', methods=['POST'])
def signup():
    
    id_receive = request.form['id_give'].upper()
    pass_receive = request.form['pass_give']
    nickname_receive = request.form['nickname_give'].upper()
    
    hashed_password = hash_pass(pass_receive,id_receive)
           
    doc = {
        'id': id_receive,
        'password': hashed_password,
        'nickname': nickname_receive
    }
    
    print(doc)
    db.users.insert_one(doc)
    
    return jsonify({'success': '가입완료!'})

@app.route('/sign/signin', methods=['POST'])
def api_signin():
    
    id_receive = request.form['id_give'].upper()
    pass_receive = request.form['pass_give']
    
    hashed_password = hash_pass(pass_receive,id_receive)
    
    user = db.users.find_one({'id':id_receive})
    
    print(user)
    
    if(hashed_password == user['password']):
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
    
        return jsonify({'success':'환영합니다.'+user['nickname']+'님','access_token':access_token, 'refresh_token':refresh_token})
    else:
        return jsonify({'fail':'ID와 비밀번호를 확인해주세요.'})

#cookie

@app.route('/set_access_token', methods=['POST'])
def set_access_token():
    user_id = request.form['id_give']
    access_token = create_access_token(identity=user_id)
    response = make_response(render_template('/sign_test.html'))
    response.set_cookie('chachaAccessToken', value=access_token) #path='/localhost', domain='/localhost', httponly=True
    
    return response
        
@app.route('/set_refresh_token', methods=['POST'])
def set_refresh_token():
    user_id = request.form['id_give']
    refresh_token = create_refresh_token(identity=user_id)
    response = make_response(render_template('/sign_test.html'))
    response.set_cookie('chachaRefreshToken', value=refresh_token)
    
    return response

@app.route('/get_access_token', methods=['GET'])
def get_access_token():
    result = request.cookies.get('chachaAccessToken')
    
    return result
        
@app.route('/get_refresh_token', methods=['GET'])
def get_refresh_token():
    result = request.cookies.get('chachaRefreshToken')
    
    return result
    
    

@app.route('/sign/change_pass', methods=['POST'])
@jwt_required
def api_change_pass():
    current_user = get_jwt_identity()
    
    print(type(current_user))
    print(current_user)
    
    pass_receive = request.form['pass_give']
    new_password = request.form['new_pass_give']
    
    hashed_password = hash_pass(pass_receive,current_user)
    new_password = hash_pass(new_password,current_user)
    
    user = db.users.find_one({'id':current_user})
    
    print(user)
    
    if(hashed_password == user['password']):
        db.users.update_one({'id':current_user},{'$set':{'password':new_password}})    
        return jsonify({'success':'비밀번호가 변경되었습니다.'})
    else:
        return jsonify({'fail':'기존 비밀번호가 틀렸습니다.'})

# @app.route('/sign/delete_user', methods=['POST'])
# @jwt_required
# def api_delete_user():
#     current_user = get_jwt_identity()
    
#     return jsonify({'success':'회원탈퇴완료'})

@app.route('/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token, current_user=current_user)

@app.route('/sign_test')
def sign_page():
   return render_template('sign_test.html')

#***************************************************************************************************
if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)