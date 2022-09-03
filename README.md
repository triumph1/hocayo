
# Hocayo
Python 3.10 + Django 4.1 + Mongodb = New Home Category


# 목표
* 홈 카테고리의 Dowant 탈출
* MongoDB 의 사용
* 시간대별 홈카의 응답을 기록, 가장 이상적인 캐싱 시간을 알아낸다.


# 개발 순서
* ~~postgres 14.5 로 데이터 마이그레이션 (django 4.1 의 최신 psycopg2 는 postgres 9 를 지원 안한다.)~~
* ~~db2 postgres 를 로커로 가져온다.~~
* 어드민 페이지를 열어본다.
* db2 postgres 를 덤프해 그대로 json 으로 바꿔서 몽고디비로 넣는다.
* 홈카 리펙터링 없이 그대로 Django 4.1 로 옮겨온다. (처음엔 로컬 포스트그리에 부착)
* Djongo 사용해서 MongoDB 로 옮겨온 뒤 모든 테스트가 통과하는지 본다.


## Djongo 의문
* Djongo 에서 pymongo 로 마이그레이션 할 수 있을까? (아니면 motor 로?, async view 쓰고 motor 쓰면 된다.)
* 나중엔 Django Ninja 깔아서 요거로 리펙터링 해도 좋겠다. Swagger 는 있어야지


