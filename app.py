from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
import jwt
import datetime
import bcrypt
import os
import requests
import random

load_dotenv()


app = Flask(__name__)
ca = certifi.where()
client = MongoClient(os.environ.get("MONGO_URI"), tlsCAFile=ca)
db = client.dbsparta_plus_week4
SECRET_KEY = os.environ.get("JWT_SECRET")

def get_image_url(path):
    base_url = "https://image.tmdb.org/t/p/w500"
    return base_url + path


def create_payload(user_id):
    """사용자 ID와 만료 시간을 포함한 JWT 페이로드 생성

    인자:
        user_id (str): 페이로드에 사용할 사용자 ID.

    반환:
        dict: 사용자 ID와 만료 시간을 포함한 페이로드.
    """
    return {'id': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}


def get_user(user_id):
    """사용자 ID로 사용자 정보 검색

    인자:
        user_id (str): 검색할 사용자 ID.

    반환:
        dict: 사용자 정보, 찾지 못할 경우 None 반환.
    """
    return db.user.find_one({'id': user_id})


def hash_password(password):
    """bcrypt를 사용하여 비밀번호 해싱

    인자:
        password (str): 해싱할 비밀번호.

    반환:
        str: 해싱된 비밀번호.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, hashed_password):
    """비밀번호와 해시된 비밀번호를 bcrypt로 확인

    인자:
        password (str): 확인할 비밀번호.
        hashed_password (str): 확인할 해싱된 비밀번호.

    반환:
        bool: 비밀번호가 확인되면 True, 그렇지 않으면 False.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


@app.route('/movie/<movie_id>')
def detail(movie_id):
    token = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_info = get_user(payload['id'])
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=ko-KR&api_key=127d1ec8dfd28bfe9f6b8d15f689cdd4"
        response = requests.get(url)
        movie = response.json()
    
        if 'success' in movie and not movie['success']:
            return redirect(url_for("home"))
        return render_template('detail.html', movie=movie, nickname=user_info['nick'], )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('login.html', msg=request.args.get("msg"))


@app.route('/')
def home():
    """홈 페이지 렌더링

    사용자가 인증된 경우 사용자의 닉네임과 함께 인덱스 페이지를 렌더링합니다.
    그렇지 않은 경우 로그인 페이지로 리디렉션합니다.

    반환:
        str: 홈 페이지의 렌더링된 HTML.
    """

    token = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_info = get_user(payload['id'])
        base_url = "https://image.tmdb.org/t/p/w780"
        url = "https://api.themoviedb.org/3/movie/popular?api_key=127d1ec8dfd28bfe9f6b8d15f689cdd4&language=ko-KR&page=1"
        response = requests.get(url)
        data = response.json()
        movies = data['results']
       


        random_index = random.randint(0, 9)
        movies = [movie for movie in data['results'] if not "Flood" in movie['title'] and not "분노의" in movie['title'] and not "가디언즈" in movie['title']]
        main = movies[random_index]
        image = base_url + main['backdrop_path']
        title = main['title']
        description = main['overview']
        data = requests.get(f"https://api.themoviedb.org/3/movie/{main['id']}/videos?language=en-US&api_key=127d1ec8dfd28bfe9f6b8d15f689cdd4").json()
        video_info = data['results'][0]

        main_video = f"https://www.youtube.com/embed/{video_info['key']}?&loop=1&playlist={video_info['key']}" if video_info["site"] == "YouTube" else f"https://vimeo.com/{video_info['key']}"
        return render_template('index.html', nickname=user_info["nick"], id=main['id'], title=title, image=image, description=description, movies=movies,main_video=main_video, main=main)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route('/login')
def login():
    """로그인 페이지 렌더링

    반환:
        str: 로그인 페이지의 렌더링된 HTML.
    """
    token = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        get_user(payload['id'])
        return redirect(url_for("home"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('login.html', msg=request.args.get("msg"))



@app.route('/register')
def register():
    """회원가입 페이지 렌더링

    반환:
        str: 회원가입 페이지의 렌더링된 HTML.
    """
    token = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        get_user(payload['id'])
        jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return redirect(url_for("home"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('register.html')
    
    
@app.route('/search')
def search():
    token = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        get_user(payload['id'])
        query = request.args.get('query')[:32]
        url = f'https://api.themoviedb.org/3/search/movie?query={query}&include_adult=false&language=ko-KR&page=1&api_key=9a7aab15ebacfa7f6be753b47a289e9a'
        response = requests.get(url)
        movies = response.json()
        filtered_movies = [
            movie for movie in movies['results']
            if movie['backdrop_path'] or movie['poster_path']
        ]

        # 필터링 된 영화 중 backdrop_path가 없으면 poster_path를 대신 사용
        for movie in filtered_movies:
            if not movie['backdrop_path'] and movie['poster_path']:
                movie['backdrop_path'] = movie['poster_path']
                del movie['poster_path']
                
            if len(movie['title']) > 20:
                movie['title'] = movie['title'][:18] + '...'
                
        print(filtered_movies[0:12])
        return render_template('search.html',count=movies['total_results'], movies=filtered_movies[0:12], query=query)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template('login.html', msg=request.args.get("msg"))


@app.route('/api/register', methods=['POST'])
def api_register():
    """제공된 ID, 비밀번호, 닉네임으로 새 사용자 회원가입

    반환:
        json: 회원가입 결과를 포함한 JSON 응답.
    """
    try:
        user_id = request.json['id_give']
        password = request.json['pw_give']
        nickname = request.json['nickname_give']

        # ID 유효성 검사
        if len(user_id) < 4 or len(user_id) > 16:
            return jsonify({'result': 'fail', 'msg': 'ID는 4~16자 사이여야 합니다.'})
        
        # 비밀번호 유효성 검사
        if len(password) < 8:
            return jsonify({'result': 'fail', 'msg': '비밀번호는 최소 8자 이상이어야 합니다.'})
        
        # 닉네임 유효성 검사
        if len(nickname) < 2 or len(nickname) > 10:
            return jsonify({'result': 'fail', 'msg': '닉네임은 2~10자 사이여야 합니다.'})

        # ID 중복 확인
        if db.user.find_one({'id': user_id}):
            return jsonify({'result': 'fail', 'msg': '이미 존재하는 ID입니다.'})
        
        # 닉네임 중복 확인
        if db.user.find_one({'nick': nickname}):
            return jsonify({'result': 'fail', 'msg': '이미 존재하는 닉네임입니다.'})

        db.user.insert_one({'id': user_id, 'pw': hash_password(password), 'nick': nickname})
        return jsonify({'result': 'success'})
    except KeyError:
        return jsonify({'result': 'fail', 'msg': '필수 항목이 누락되었습니다.'})

    


@app.route('/api/login', methods=['POST'])
def api_login():
    """제공된 ID와 비밀번호로 사용자 인증

    반환:
        json: 인증 결과를 포함한 JSON 응답.
    """
    try:
        user_id = request.json['id_give']
        password = request.json['pw_give']
        user = get_user(user_id)

        if user and verify_password(password, user['pw']):
            token = jwt.encode(create_payload(user_id), SECRET_KEY, algorithm='HS256')
            return jsonify({'result': 'success', 'token': token})

        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'}), 401
    except KeyError:
        return jsonify({'result': 'fail', 'msg': '아이디와 비밀번호는 비어있지 않아야합니다.'}), 401



@app.route('/api/nick', methods=['GET'])
def api_valid():
    """사용자의 인증 토큰을 검증하고 닉네임을 가져옵니다.

    반환:
        json: 검증 결과를 포함한 JSON 응답.
    """
    token = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_info = get_user(payload['id'])
        return jsonify({'result': 'success', 'nickname': user_info['nick']})
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'}), 401
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'}), 401


# 댓글 입력하기
@app.route('/comment', methods=["POST"])
def comment():
    comment_receive = request.form['comment_give']
    user_id_receive = request.form['user_id_give']
    movie_id_receive = request.form['movie_id_give']
    comment_id_receive = request.form['comment_id_give']

    doc = {
        'user' : user_id_receive,
        'comment' : comment_receive,
        'movie' : movie_id_receive,
        'commentId' : comment_id_receive
    }
    db.comment.insert_one(doc)
    return jsonify({'msg' : '댓글 등록완료!'})

# 댓글 불러오기
@app.route('/comment/movie/<movie_id>/', methods=["GET"])
def comments_get(movie_id):
    comments = list(db.comment.find({"movie": movie_id},{"_id":False}))
    return jsonify({'result':comments})

# 댓글 수정하기
@app.route('/comment/update', methods=["POST"])
def comment_update():
    comment_id_receive = request.form['commentId']
    comment_receive = request.form['comment']
    db.comment.update_one({"commentId" : comment_id_receive}, {'$set' : {'comment' : comment_receive}})
    return jsonify({'msg': "수정 완료"})

# 댓글 삭제하기
@app.route('/comment/delete', methods=["DELETE"])
def comment_delete():
    comment_receive = request.form['commentId']
    db.comment.delete_one({"commentId" : comment_receive})
    return jsonify({'msg' : '댓글 삭제 완료'})
    


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)